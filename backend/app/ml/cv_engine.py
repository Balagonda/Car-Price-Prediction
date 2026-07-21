"""
AutoWorth AI — Computer Vision Engine

Full YOLO + OpenCV vehicle analysis pipeline:
  1. Decode and validate image bytes
  2. YOLO vehicle detection (YOLOv8n, graceful fallback to OpenCV-only)
  3. Geometric ROI part segmentation (bumper, hood, doors, fender, windshield)
  4. Per-part damage scoring via edge density, colour anomaly, texture entropy
  5. Severity classification: Minor | Moderate | Severe per part
  6. Aggregated overall severity
  7. Heatmap generation — coloured overlay bounding boxes, legend, alpha blend
  8. Repair cost estimation using Indian market heuristics

Graceful degradation:
  - If `ultralytics` / `torch` is not installed, YOLO step is skipped.
    OpenCV-only analysis still produces a valid result.
  - If vehicle detection confidence is low, analysis continues on full frame.

Layer: ML Layer
"""

from __future__ import annotations

import io
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

# cv2 and numpy are imported lazily inside methods so this module loads
# cleanly even when OpenCV is not installed (graceful degradation).
try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    np = None   # type: ignore[assignment]
    _CV2_AVAILABLE = False

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# COCO class index for "car" in YOLOv8 pre-trained weights
_YOLO_CAR_CLASS_IDS: frozenset[int] = frozenset({2, 5, 7})  # car, bus, truck

# Minimum YOLO confidence threshold
_YOLO_CONF_THRESHOLD: float = 0.30

# Damage scoring thresholds (0.0–1.0 composite score)
_SCORE_MINOR_THRESHOLD: float = 0.20
_SCORE_MODERATE_THRESHOLD: float = 0.45

# ── Repair Cost Matrix (INR) ─────────────────────────────────────────────────
# {part_name: {severity: (min_cost, max_cost)}}
_REPAIR_COST_MATRIX: dict[str, dict[str, tuple[int, int]]] = {
    "Front Bumper": {
        "Minor": (3_000, 8_000),
        "Moderate": (10_000, 25_000),
        "Severe": (30_000, 60_000),
    },
    "Rear Bumper": {
        "Minor": (3_000, 7_000),
        "Moderate": (9_000, 22_000),
        "Severe": (28_000, 55_000),
    },
    "Hood": {
        "Minor": (5_000, 12_000),
        "Moderate": (15_000, 35_000),
        "Severe": (40_000, 80_000),
    },
    "Left Door": {
        "Minor": (4_000, 10_000),
        "Moderate": (12_000, 30_000),
        "Severe": (35_000, 70_000),
    },
    "Right Door": {
        "Minor": (4_000, 10_000),
        "Moderate": (12_000, 30_000),
        "Severe": (35_000, 70_000),
    },
    "Left Fender": {
        "Minor": (3_500, 9_000),
        "Moderate": (11_000, 28_000),
        "Severe": (32_000, 65_000),
    },
    "Right Fender": {
        "Minor": (3_500, 9_000),
        "Moderate": (11_000, 28_000),
        "Severe": (32_000, 65_000),
    },
    "Windshield": {
        "Minor": (8_000, 15_000),
        "Moderate": (18_000, 35_000),
        "Severe": (40_000, 90_000),
    },
    "Roof": {
        "Minor": (6_000, 14_000),
        "Moderate": (18_000, 40_000),
        "Severe": (45_000, 1_00_000),
    },
}

# ── Heatmap Colours (BGR) ────────────────────────────────────────────────────
_COLOUR_OK: tuple[int, int, int] = (0, 200, 60)         # Green
_COLOUR_MINOR: tuple[int, int, int] = (0, 215, 255)     # Amber-yellow
_COLOUR_MODERATE: tuple[int, int, int] = (0, 140, 255)  # Orange
_COLOUR_SEVERE: tuple[int, int, int] = (30, 30, 220)    # Red

# ── Vehicle Type Classification ──────────────────────────────────────────────
# Mapped by bounding box aspect ratio (width/height)
_VEHICLE_TYPES: list[tuple[float, float, str]] = [
    (0.0, 0.95, "Hatchback"),
    (0.95, 1.25, "Sedan"),
    (1.25, 2.50, "SUV"),
    (2.50, 99.0, "Commercial"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PartAnalysis:
    """Result of damage analysis for one vehicle body part."""

    part_name: str
    severity: str                    # "None" | "Minor" | "Moderate" | "Severe"
    damage_score: float              # Raw composite 0.0–1.0
    repair_cost_min: int
    repair_cost_max: int
    bbox: tuple[int, int, int, int]  # (x, y, w, h) in image coords
    is_damaged: bool


@dataclass
class CVAnalysisResult:
    """Structured output from CVEngine.analyze()."""

    vehicle_detected: bool
    vehicle_type: str | None
    vehicle_bbox: tuple[int, int, int, int] | None  # (x, y, w, h)
    overall_severity: str            # "None" | "Minor" | "Moderate" | "Severe"
    damage_level: str                # Alias for overall_severity (DB enum value)
    damaged_parts: list[str]
    part_analyses: list[PartAnalysis] = field(default_factory=list)
    total_repair_cost_min: int = 0
    total_repair_cost_max: int = 0
    total_repair_cost_estimate: float = 0.0
    heatmap_bytes: bytes | None = None
    raw_detections: dict[str, Any] = field(default_factory=dict)
    yolo_available: bool = False
    processing_notes: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# CVEngine
# ─────────────────────────────────────────────────────────────────────────────

class CVValidationError(Exception):
    """Raised when image bytes cannot be decoded or fail resolution checks."""


class CVEngine:
    """
    Computer Vision pipeline for vehicle image analysis.

    Instantiate once (e.g., on startup), then call analyze() per request.
    The YOLO model is loaded lazily on the first analyze() call.
    """

    _yolo_model: Any = None          # ultralytics.YOLO instance or None
    _yolo_attempted: bool = False    # Avoid repeated import failures

    def __init__(self, yolo_weights_path: str | None = None) -> None:
        self._weights_path = yolo_weights_path

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(
        self,
        image_bytes: bytes,
        angle: str = "Front",
    ) -> CVAnalysisResult:
        """
        Analyse a vehicle image and return structured CV results.

        Args:
            image_bytes: Raw image bytes (JPEG / PNG / WebP).
            angle: Image angle label (for logging and heuristics).

        Returns:
            CVAnalysisResult dataclass.

        Raises:
            CVValidationError: If image cannot be decoded or is too small.
        """
        notes: list[str] = []

        # ── Guard: cv2 must be available ──────────────────────
        if not _CV2_AVAILABLE or cv2 is None:
            raise CVValidationError(
                "OpenCV (cv2) is not installed. "
                "Run: pip install opencv-python-headless"
            )

        # ── Step 1: Decode image ──────────────────────────────
        bgr_image = self._decode_image(image_bytes)
        h, w = bgr_image.shape[:2]
        if w < 100 or h < 100:
            raise CVValidationError(
                f"Decoded image {w}×{h} is too small for analysis (min 100×100)."
            )

        # ── Step 2: YOLO vehicle detection ────────────────────
        yolo_available = self._try_load_yolo()
        vehicle_bbox: tuple[int, int, int, int] | None = None
        vehicle_detected = False
        vehicle_type: str | None = None

        if yolo_available and self._yolo_model is not None:
            vehicle_bbox, vehicle_detected = self._run_yolo_detection(bgr_image)
            notes.append("YOLO detection: active")
        else:
            # Fallback: assume vehicle occupies centre 90% of frame
            margin_x = int(w * 0.05)
            margin_y = int(h * 0.05)
            vehicle_bbox = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)
            vehicle_detected = True  # Assume vehicle present; user uploaded intentionally
            notes.append("YOLO unavailable — full-frame OpenCV fallback active")

        # ── Step 3: Vehicle type classification ───────────────
        if vehicle_bbox:
            bx, by, bw, bh = vehicle_bbox
            aspect = bw / max(bh, 1)
            vehicle_type = self._classify_vehicle_type(aspect)
        else:
            vehicle_type = "Unknown"

        # ── Step 4: Part segmentation + damage analysis ───────
        if not vehicle_bbox:
            vehicle_bbox = (0, 0, w, h)

        parts = self._segment_and_analyse_parts(bgr_image, vehicle_bbox, angle)

        # ── Step 5: Aggregate severity ────────────────────────
        overall_severity = self._aggregate_severity(parts)

        # ── Step 6: Repair cost totals ────────────────────────
        damaged_parts = [p.part_name for p in parts if p.is_damaged]
        total_min = sum(p.repair_cost_min for p in parts if p.is_damaged)
        total_max = sum(p.repair_cost_max for p in parts if p.is_damaged)
        total_estimate = (total_min + total_max) / 2.0

        # ── Step 7: Generate heatmap ──────────────────────────
        heatmap_bytes = self._generate_heatmap(bgr_image.copy(), parts, vehicle_bbox)

        logger.info(
            "🔍 [CVEngine] Analysis complete — angle=%s vehicle=%s type=%s "
            "severity=%s damaged_parts=%d repair=₹%.0f",
            angle,
            vehicle_detected,
            vehicle_type,
            overall_severity,
            len(damaged_parts),
            total_estimate,
        )

        return CVAnalysisResult(
            vehicle_detected=vehicle_detected,
            vehicle_type=vehicle_type,
            vehicle_bbox=vehicle_bbox,
            overall_severity=overall_severity,
            damage_level=overall_severity,
            damaged_parts=damaged_parts,
            part_analyses=parts,
            total_repair_cost_min=total_min,
            total_repair_cost_max=total_max,
            total_repair_cost_estimate=total_estimate,
            heatmap_bytes=heatmap_bytes,
            raw_detections={
                "yolo_available": yolo_available,
                "vehicle_bbox": vehicle_bbox,
                "parts_analysed": len(parts),
            },
            yolo_available=yolo_available,
            processing_notes=notes,
        )

    # ── YOLO Helpers ──────────────────────────────────────────────────────────

    def _try_load_yolo(self) -> bool:
        """
        Attempt to load YOLOv8 model lazily.
        Returns True if model is available, False otherwise.
        """
        if self._yolo_attempted:
            return self._yolo_model is not None

        self._yolo_attempted = True
        try:
            from ultralytics import YOLO  # type: ignore[import]

            weights = self._weights_path or "yolov8n.pt"
            self._yolo_model = YOLO(weights)
            logger.info("✅ [CVEngine] YOLOv8 loaded — weights=%s", weights)
            return True
        except ImportError:
            logger.warning(
                "⚠️  [CVEngine] ultralytics not installed — using OpenCV-only fallback"
            )
            return False
        except Exception as exc:
            logger.warning("⚠️  [CVEngine] YOLO load failed: %s — using fallback", exc)
            return False

    def _run_yolo_detection(
        self, bgr: np.ndarray
    ) -> tuple[tuple[int, int, int, int] | None, bool]:
        """
        Run YOLOv8 inference; extract the highest-confidence car bbox.

        Returns:
            (bbox_xywh, vehicle_detected)
        """
        try:
            results = self._yolo_model(bgr, conf=_YOLO_CONF_THRESHOLD, verbose=False)
            best_box = None
            best_conf = 0.0

            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    if cls_id in _YOLO_CAR_CLASS_IDS and conf > best_conf:
                        best_conf = conf
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                        best_box = (x1, y1, x2 - x1, y2 - y1)

            if best_box:
                logger.debug(
                    "🚗 [CVEngine] YOLO: vehicle detected conf=%.2f bbox=%s",
                    best_conf,
                    best_box,
                )
                return best_box, True

            logger.debug("🚗 [CVEngine] YOLO: no vehicle detected at conf=%.2f", _YOLO_CONF_THRESHOLD)
            # Fall back to full frame if nothing detected
            h, w = bgr.shape[:2]
            margin_x, margin_y = int(w * 0.05), int(h * 0.05)
            return (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y), False
        except Exception as exc:
            logger.warning("⚠️  [CVEngine] YOLO inference failed: %s", exc)
            h, w = bgr.shape[:2]
            return (0, 0, w, h), False

    # ── Part Segmentation ─────────────────────────────────────────────────────

    def _segment_and_analyse_parts(
        self,
        bgr: np.ndarray,
        vehicle_bbox: tuple[int, int, int, int],
        angle: str,
    ) -> list[PartAnalysis]:
        """
        Divide the vehicle bounding box into named part ROIs.
        Apply damage scoring to each ROI.

        ROI layout (relative to vehicle bbox, as fractions):
          Front view:  Front Bumper, Hood, Windshield, Left Fender, Right Fender
          Rear view:   Rear Bumper, Roof, Left Fender, Right Fender
          Side views:  Left/Right Door, Hood, Left/Right Fender, Roof
          Interior:    simplified — no external body parts
        """
        vx, vy, vw, vh = vehicle_bbox
        parts: list[PartAnalysis] = []

        # Define part layout per angle
        part_rois = self._get_part_rois(vx, vy, vw, vh, angle)

        for part_name, roi in part_rois.items():
            rx, ry, rw, rh = roi
            # Clamp to image bounds
            img_h, img_w = bgr.shape[:2]
            rx = max(0, rx)
            ry = max(0, ry)
            rw = min(rw, img_w - rx)
            rh = min(rh, img_h - ry)

            if rw <= 10 or rh <= 10:
                continue

            roi_crop = bgr[ry : ry + rh, rx : rx + rw]
            score = self._compute_damage_score(roi_crop)
            severity = self._score_to_severity(score)
            is_damaged = severity != "None"

            cost_range = _REPAIR_COST_MATRIX.get(part_name, {}).get(
                severity, (0, 0)
            )

            parts.append(
                PartAnalysis(
                    part_name=part_name,
                    severity=severity,
                    damage_score=round(score, 4),
                    repair_cost_min=cost_range[0],
                    repair_cost_max=cost_range[1],
                    bbox=(rx, ry, rw, rh),
                    is_damaged=is_damaged,
                )
            )

        return parts

    def _get_part_rois(
        self, vx: int, vy: int, vw: int, vh: int, angle: str
    ) -> dict[str, tuple[int, int, int, int]]:
        """
        Return a dict of {part_name: (x, y, w, h)} based on viewing angle.
        Coordinates are in image pixel space.
        """
        angle_lower = angle.lower()

        if "rear" in angle_lower:
            return {
                "Rear Bumper": (vx, vy + int(vh * 0.72), vw, int(vh * 0.28)),
                "Roof":        (vx, vy, vw, int(vh * 0.25)),
                "Left Fender": (vx, vy + int(vh * 0.25), int(vw * 0.25), int(vh * 0.47)),
                "Right Fender":(vx + int(vw * 0.75), vy + int(vh * 0.25), int(vw * 0.25), int(vh * 0.47)),
            }
        elif "left" in angle_lower:
            return {
                "Left Door":   (vx + int(vw * 0.25), vy + int(vh * 0.30), int(vw * 0.50), int(vh * 0.55)),
                "Left Fender": (vx, vy + int(vh * 0.30), int(vw * 0.25), int(vh * 0.55)),
                "Hood":        (vx, vy, int(vw * 0.40), int(vh * 0.30)),
                "Roof":        (vx + int(vw * 0.15), vy, int(vw * 0.70), int(vh * 0.30)),
                "Rear Bumper": (vx + int(vw * 0.75), vy + int(vh * 0.70), int(vw * 0.25), int(vh * 0.30)),
            }
        elif "right" in angle_lower:
            return {
                "Right Door":  (vx + int(vw * 0.25), vy + int(vh * 0.30), int(vw * 0.50), int(vh * 0.55)),
                "Right Fender":(vx + int(vw * 0.75), vy + int(vh * 0.30), int(vw * 0.25), int(vh * 0.55)),
                "Hood":        (vx + int(vw * 0.60), vy, int(vw * 0.40), int(vh * 0.30)),
                "Roof":        (vx + int(vw * 0.15), vy, int(vw * 0.70), int(vh * 0.30)),
                "Front Bumper":(vx, vy + int(vh * 0.70), int(vw * 0.25), int(vh * 0.30)),
            }
        elif "interior" in angle_lower:
            return {
                "Windshield": (vx, vy, vw, int(vh * 0.40)),
                "Roof":       (vx, vy + int(vh * 0.40), vw, int(vh * 0.20)),
            }
        else:
            # Default: Front view
            return {
                "Front Bumper": (vx, vy + int(vh * 0.70), vw, int(vh * 0.30)),
                "Hood":         (vx + int(vw * 0.15), vy, int(vw * 0.70), int(vh * 0.40)),
                "Windshield":   (vx + int(vw * 0.20), vy + int(vh * 0.10), int(vw * 0.60), int(vh * 0.35)),
                "Left Fender":  (vx, vy + int(vh * 0.25), int(vw * 0.18), int(vh * 0.50)),
                "Right Fender": (vx + int(vw * 0.82), vy + int(vh * 0.25), int(vw * 0.18), int(vh * 0.50)),
            }

    # ── Damage Scoring ────────────────────────────────────────────────────────

    def _compute_damage_score(self, roi: np.ndarray) -> float:
        """
        Compute a composite 0.0–1.0 damage score for a ROI using three signals:

        1. Edge Density  — Canny edge detection; high density = structural damage
        2. Colour Anomaly — HSV saturation spike = rust, paint transfer
        3. Texture Entropy — high local entropy = scratches, dents

        Weighted average: edge (0.45) + colour (0.30) + entropy (0.25)
        """
        if roi.size == 0:
            return 0.0

        # ── Signal 1: Edge density ─────────────────────────────
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blurred, threshold1=50, threshold2=150)
        edge_density = float(np.count_nonzero(edges)) / max(edges.size, 1)
        # Normalise: typical undamaged panels ~0.03, damaged ~0.12+
        edge_score = min(edge_density / 0.15, 1.0)

        # ── Signal 2: Colour anomaly (HSV saturation spike) ────
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        sat_channel = hsv[:, :, 1].astype(float) / 255.0
        # High mean saturation in a region may indicate rust or paint transfer
        mean_sat = float(np.mean(sat_channel))
        # Also detect high variance (blotchy discolouration)
        var_sat = float(np.var(sat_channel))
        colour_score = min((mean_sat * 0.5 + var_sat * 5.0), 1.0)

        # ── Signal 3: Texture entropy ─────────────────────────
        entropy_score = self._compute_entropy_score(gray)

        composite = (
            edge_score * 0.45
            + colour_score * 0.30
            + entropy_score * 0.25
        )
        return min(float(composite), 1.0)

    def _compute_entropy_score(self, gray: np.ndarray) -> float:
        """
        Approximate Shannon entropy of local texture blocks.
        Uses histogram entropy as a proxy; avoids scipy dependency.
        """
        try:
            # Divide into 4×4 grid of blocks and measure histogram entropy per block
            h, w = gray.shape
            bh = max(h // 4, 1)
            bw = max(w // 4, 1)
            entropies: list[float] = []

            for r in range(0, h, bh):
                for c in range(0, w, bw):
                    block = gray[r : r + bh, c : c + bw]
                    if block.size < 4:
                        continue
                    hist, _ = np.histogram(block.ravel(), bins=32, range=(0, 256))
                    hist = hist.astype(float)
                    total = hist.sum()
                    if total == 0:
                        continue
                    prob = hist / total
                    prob = prob[prob > 0]
                    entropy = float(-np.sum(prob * np.log2(prob)))
                    entropies.append(entropy)

            if not entropies:
                return 0.0

            mean_entropy = float(np.mean(entropies))
            # Max theoretical entropy for 32-bin histogram = log2(32) = 5.0
            return min(mean_entropy / 5.0, 1.0)
        except Exception:
            return 0.0

    # ── Classification Helpers ────────────────────────────────────────────────

    @staticmethod
    def _score_to_severity(score: float) -> str:
        """Map composite damage score to severity label."""
        if score < _SCORE_MINOR_THRESHOLD:
            return "None"
        elif score < _SCORE_MODERATE_THRESHOLD:
            return "Minor"
        elif score < 0.70:
            return "Moderate"
        else:
            return "Severe"

    @staticmethod
    def _classify_vehicle_type(aspect_ratio: float) -> str:
        """Classify vehicle type based on bounding box aspect ratio."""
        for min_ar, max_ar, label in _VEHICLE_TYPES:
            if min_ar <= aspect_ratio < max_ar:
                return label
        return "SUV"

    @staticmethod
    def _aggregate_severity(parts: list[PartAnalysis]) -> str:
        """
        Overall severity = worst severity across all parts.
        Tie-break (multiple Moderate vs one Severe): Severe always wins.
        """
        order = {"None": 0, "Minor": 1, "Moderate": 2, "Severe": 3}
        worst = "None"
        for p in parts:
            if order.get(p.severity, 0) > order.get(worst, 0):
                worst = p.severity
        return worst

    # ── Heatmap Generation ────────────────────────────────────────────────────

    def _generate_heatmap(
        self,
        bgr: np.ndarray,
        parts: list[PartAnalysis],
        vehicle_bbox: tuple[int, int, int, int],
    ) -> bytes:
        """
        Generate a heatmap overlay image:
        - Draw coloured bounding boxes per part (severity-coded colours)
        - Alpha-blend a heat tint over damaged ROIs
        - Add part labels and a severity legend

        Returns PNG bytes.
        """
        overlay = bgr.copy()

        severity_colour_map = {
            "None": _COLOUR_OK,
            "Minor": _COLOUR_MINOR,
            "Moderate": _COLOUR_MODERATE,
            "Severe": _COLOUR_SEVERE,
        }

        # ── Draw part ROI boxes ────────────────────────────────
        for part in parts:
            colour = severity_colour_map.get(part.severity, _COLOUR_OK)
            px, py, pw, ph = part.bbox
            thickness = 2 if part.severity == "None" else 3

            # Alpha tint for damaged regions
            if part.is_damaged:
                tint = overlay[py : py + ph, px : px + pw].copy()
                tint_layer = np.full_like(tint, colour, dtype=np.uint8)
                alpha = 0.18 if part.severity == "Minor" else (
                    0.28 if part.severity == "Moderate" else 0.40
                )
                blended = cv2.addWeighted(tint, 1 - alpha, tint_layer, alpha, 0)
                overlay[py : py + ph, px : px + pw] = blended

            # Draw rectangle
            cv2.rectangle(overlay, (px, py), (px + pw, py + ph), colour, thickness)

            # Part label
            label = f"{part.part_name}: {part.severity}"
            font_scale = 0.42
            font = cv2.FONT_HERSHEY_SIMPLEX
            (lw, lh), _ = cv2.getTextSize(label, font, font_scale, 1)
            label_y = max(py - 5, lh + 5)

            # Background pill for readability
            cv2.rectangle(
                overlay,
                (px, label_y - lh - 4),
                (px + lw + 6, label_y + 2),
                colour,
                -1,
            )
            cv2.putText(
                overlay,
                label,
                (px + 3, label_y - 2),
                font,
                font_scale,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        # ── Draw vehicle bbox outline ──────────────────────────
        vx, vy, vw, vh = vehicle_bbox
        cv2.rectangle(overlay, (vx, vy), (vx + vw, vy + vh), (200, 200, 200), 1)

        # ── Legend ─────────────────────────────────────────────
        overlay = self._draw_legend(overlay)

        # ── Encode to PNG bytes ────────────────────────────────
        success, buffer = cv2.imencode(".png", overlay)
        if not success:
            # Fallback: return original frame as PNG
            success, buffer = cv2.imencode(".png", bgr)
        return bytes(buffer.tobytes())

    @staticmethod
    def _draw_legend(bgr: np.ndarray) -> np.ndarray:
        """Draw a severity colour legend in the bottom-right corner."""
        h, w = bgr.shape[:2]
        legend_items = [
            ("No Damage", _COLOUR_OK),
            ("Minor",     _COLOUR_MINOR),
            ("Moderate",  _COLOUR_MODERATE),
            ("Severe",    _COLOUR_SEVERE),
        ]
        box_w, box_h = 130, len(legend_items) * 22 + 10
        lx = w - box_w - 10
        ly = h - box_h - 10

        # Semi-transparent background
        sub = bgr[ly : ly + box_h, lx : lx + box_w]
        bg = np.zeros_like(sub)
        blended = cv2.addWeighted(sub, 0.45, bg, 0.55, 0)
        bgr[ly : ly + box_h, lx : lx + box_w] = blended

        for i, (label, colour) in enumerate(legend_items):
            item_y = ly + 8 + i * 22
            cv2.rectangle(bgr, (lx + 6, item_y), (lx + 18, item_y + 12), colour, -1)
            cv2.putText(
                bgr,
                label,
                (lx + 24, item_y + 11),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (230, 230, 230),
                1,
                cv2.LINE_AA,
            )
        return bgr

    # ── Image Decoding ────────────────────────────────────────────────────────

    @staticmethod
    def _decode_image(image_bytes: bytes) -> np.ndarray:
        """
        Decode raw image bytes to a BGR numpy array.

        Tries OpenCV first; falls back to Pillow for WebP and other formats.

        Raises:
            CVValidationError: if decoding fails.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if bgr is None:
            # Fallback via Pillow
            try:
                pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as exc:
                raise CVValidationError(
                    f"Cannot decode image bytes — not a valid image format: {exc}"
                ) from exc

        if bgr is None:
            raise CVValidationError("Image decoding produced an empty frame.")

        return bgr
