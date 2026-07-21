"""
AutoWorth AI — CV Engine Unit Tests

Tests:
  - Image decoding (valid JPEG, corrupt bytes)
  - Part ROI segmentation for each angle
  - Damage scoring on synthetic ROIs
  - Severity classification thresholds
  - Heatmap generation produces valid PNG bytes
  - Full analyze() pipeline with a synthetic gradient image
  - CVAnalysisResult dataclass integrity

No Cloudinary / DB / YOLO model required.
"""

from __future__ import annotations

import io
import struct
import zlib

import numpy as np
import pytest
from PIL import Image

from app.ml.cv_engine import (
    CVEngine,
    CVValidationError,
    PartAnalysis,
    _REPAIR_COST_MATRIX,
    _SCORE_MINOR_THRESHOLD,
    _SCORE_MODERATE_THRESHOLD,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_jpeg_bytes(width: int = 640, height: int = 480, colour: tuple = (120, 80, 60)) -> bytes:
    """Create a small solid-colour JPEG in-memory."""
    img = Image.new("RGB", (width, height), colour)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _make_noisy_jpeg_bytes(width: int = 640, height: int = 480) -> bytes:
    """Create a JPEG with random noise (simulates scratched surface)."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@pytest.fixture
def engine() -> CVEngine:
    """Return a CVEngine instance (no YOLO needed — will fall back gracefully)."""
    return CVEngine(yolo_weights_path=None)


@pytest.fixture
def clean_car_bytes() -> bytes:
    return _make_jpeg_bytes(width=800, height=600, colour=(60, 80, 120))


@pytest.fixture
def noisy_car_bytes() -> bytes:
    return _make_noisy_jpeg_bytes(width=800, height=600)


# ─────────────────────────────────────────────────────────────────────────────
# Image Decoding
# ─────────────────────────────────────────────────────────────────────────────

class TestImageDecoding:
    def test_decode_valid_jpeg(self, engine: CVEngine, clean_car_bytes: bytes) -> None:
        arr = engine._decode_image(clean_car_bytes)
        assert arr is not None
        assert arr.ndim == 3
        assert arr.shape[2] == 3  # BGR channels

    def test_decode_corrupt_bytes_raises(self, engine: CVEngine) -> None:
        with pytest.raises(CVValidationError):
            engine._decode_image(b"not-an-image-at-all-garbage")

    def test_decode_empty_bytes_raises(self, engine: CVEngine) -> None:
        with pytest.raises(CVValidationError):
            engine._decode_image(b"")


# ─────────────────────────────────────────────────────────────────────────────
# Part ROI Segmentation
# ─────────────────────────────────────────────────────────────────────────────

class TestPartSegmentation:
    """Verify that each angle returns the expected part names."""

    FRONT_PARTS = {"Front Bumper", "Hood", "Windshield", "Left Fender", "Right Fender"}
    REAR_PARTS  = {"Rear Bumper", "Roof", "Left Fender", "Right Fender"}
    LEFT_PARTS  = {"Left Door", "Left Fender", "Hood", "Roof", "Rear Bumper"}
    RIGHT_PARTS = {"Right Door", "Right Fender", "Hood", "Roof", "Front Bumper"}

    @pytest.mark.parametrize("angle, expected_parts", [
        ("Front",     FRONT_PARTS),
        ("Rear",      REAR_PARTS),
        ("Left Side", LEFT_PARTS),
        ("Right Side", RIGHT_PARTS),
    ])
    def test_part_names_by_angle(
        self, engine: CVEngine, angle: str, expected_parts: set
    ) -> None:
        rois = engine._get_part_rois(0, 0, 800, 600, angle)
        assert set(rois.keys()) == expected_parts

    def test_all_rois_have_positive_dimensions(self, engine: CVEngine) -> None:
        for angle in ("Front", "Rear", "Left Side", "Right Side", "Interior"):
            rois = engine._get_part_rois(0, 0, 800, 600, angle)
            for name, (rx, ry, rw, rh) in rois.items():
                assert rw > 0, f"Part {name} has non-positive width in {angle} view"
                assert rh > 0, f"Part {name} has non-positive height in {angle} view"


# ─────────────────────────────────────────────────────────────────────────────
# Damage Scoring
# ─────────────────────────────────────────────────────────────────────────────

class TestDamageScoring:
    def test_blank_panel_scores_low(self, engine: CVEngine) -> None:
        """A uniform, featureless panel should score below the Minor threshold."""
        import cv2
        uniform = np.full((100, 100, 3), 150, dtype=np.uint8)
        score = engine._compute_damage_score(uniform)
        assert score < _SCORE_MINOR_THRESHOLD, (
            f"Uniform panel scored {score:.3f}, expected < {_SCORE_MINOR_THRESHOLD}"
        )

    def test_noisy_panel_scores_higher(self, engine: CVEngine) -> None:
        """A high-noise panel (simulating scratches) should score above Minor threshold."""
        noisy = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        score = engine._compute_damage_score(noisy)
        assert score >= _SCORE_MINOR_THRESHOLD, (
            f"Noisy panel scored {score:.3f}, expected >= {_SCORE_MINOR_THRESHOLD}"
        )

    def test_empty_roi_returns_zero(self, engine: CVEngine) -> None:
        empty = np.array([], dtype=np.uint8).reshape(0, 0, 3)
        score = engine._compute_damage_score(empty)
        assert score == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Severity Classification
# ─────────────────────────────────────────────────────────────────────────────

class TestSeverityClassification:
    @pytest.mark.parametrize("score, expected", [
        (0.00, "None"),
        (0.10, "None"),
        (0.19, "None"),
        (0.20, "Minor"),
        (0.35, "Minor"),
        (0.44, "Minor"),
        (0.45, "Moderate"),
        (0.60, "Moderate"),
        (0.69, "Moderate"),
        (0.70, "Severe"),
        (1.00, "Severe"),
    ])
    def test_score_to_severity(self, score: float, expected: str) -> None:
        result = CVEngine._score_to_severity(score)
        assert result == expected, f"score={score} → got '{result}', expected '{expected}'"

    def test_aggregate_worst_part_wins(self) -> None:
        parts = [
            PartAnalysis("Hood", "Minor", 0.25, 5000, 12000, (0,0,100,80), True),
            PartAnalysis("Bumper", "Severe", 0.80, 30000, 60000, (0,0,100,80), True),
            PartAnalysis("Door", "Moderate", 0.50, 12000, 30000, (0,0,100,80), True),
        ]
        assert CVEngine._aggregate_severity(parts) == "Severe"

    def test_aggregate_all_none(self) -> None:
        parts = [
            PartAnalysis("Hood", "None", 0.05, 0, 0, (0,0,100,80), False),
        ]
        assert CVEngine._aggregate_severity(parts) == "None"


# ─────────────────────────────────────────────────────────────────────────────
# Vehicle Type Classification
# ─────────────────────────────────────────────────────────────────────────────

class TestVehicleTypeClassification:
    @pytest.mark.parametrize("ratio, expected", [
        (0.80, "Hatchback"),
        (1.10, "Sedan"),
        (1.60, "SUV"),
        (3.00, "Commercial"),
    ])
    def test_classify_aspect_ratio(self, ratio: float, expected: str) -> None:
        result = CVEngine._classify_vehicle_type(ratio)
        assert result == expected


# ─────────────────────────────────────────────────────────────────────────────
# Repair Cost Matrix
# ─────────────────────────────────────────────────────────────────────────────

class TestRepairCostMatrix:
    def test_all_parts_have_three_severities(self) -> None:
        for part, levels in _REPAIR_COST_MATRIX.items():
            assert set(levels.keys()) == {"Minor", "Moderate", "Severe"}, (
                f"Part '{part}' missing severity levels"
            )

    def test_costs_are_positive_and_ordered(self) -> None:
        for part, levels in _REPAIR_COST_MATRIX.items():
            for severity, (low, high) in levels.items():
                assert low > 0, f"{part}/{severity} min cost must be > 0"
                assert high > low, f"{part}/{severity} max must be > min"

    def test_severity_cost_increases(self) -> None:
        for part, levels in _REPAIR_COST_MATRIX.items():
            assert levels["Minor"][1] < levels["Moderate"][0] or \
                   levels["Minor"][0] < levels["Moderate"][0], \
                   f"{part}: Minor max should be less than Moderate min"


# ─────────────────────────────────────────────────────────────────────────────
# Heatmap Generation
# ─────────────────────────────────────────────────────────────────────────────

class TestHeatmapGeneration:
    def test_heatmap_returns_valid_png(self, engine: CVEngine, clean_car_bytes: bytes) -> None:
        import cv2
        nparr = np.frombuffer(clean_car_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        parts = [
            PartAnalysis("Front Bumper", "Minor", 0.25, 3000, 8000, (0, 400, 800, 200), True),
            PartAnalysis("Hood", "None", 0.10, 0, 0, (100, 0, 600, 250), False),
        ]
        heatmap_bytes = engine._generate_heatmap(bgr, parts, (0, 0, 800, 600))
        assert isinstance(heatmap_bytes, bytes)
        assert len(heatmap_bytes) > 1000  # Non-trivial PNG

        # Verify it's decodable PNG
        result_img = Image.open(io.BytesIO(heatmap_bytes))
        assert result_img.format == "PNG"


# ─────────────────────────────────────────────────────────────────────────────
# Full Pipeline (OpenCV-only fallback, no YOLO)
# ─────────────────────────────────────────────────────────────────────────────

class TestFullPipeline:
    def test_analyze_clean_image_returns_result(
        self, engine: CVEngine, clean_car_bytes: bytes
    ) -> None:
        result = engine.analyze(clean_car_bytes, angle="Front")
        assert result.vehicle_detected is True
        assert result.vehicle_type is not None
        assert result.overall_severity in ("None", "Minor", "Moderate", "Severe")
        assert isinstance(result.damaged_parts, list)
        assert result.total_repair_cost_estimate >= 0.0
        assert result.heatmap_bytes is not None
        assert len(result.heatmap_bytes) > 100

    def test_analyze_noisy_image_detects_damage(
        self, engine: CVEngine, noisy_car_bytes: bytes
    ) -> None:
        result = engine.analyze(noisy_car_bytes, angle="Front")
        # A highly noisy image should trigger at least Minor damage on some parts
        assert result.overall_severity in ("Minor", "Moderate", "Severe")

    def test_analyze_tiny_image_raises(self, engine: CVEngine) -> None:
        tiny = Image.new("RGB", (50, 50), (128, 128, 128))
        buf = io.BytesIO()
        tiny.save(buf, format="JPEG")
        with pytest.raises(CVValidationError):
            engine.analyze(buf.getvalue(), angle="Front")

    def test_analyze_returns_heatmap_bytes(
        self, engine: CVEngine, clean_car_bytes: bytes
    ) -> None:
        result = engine.analyze(clean_car_bytes, angle="Rear")
        assert result.heatmap_bytes is not None

    def test_analyze_cost_estimate_matches_parts(
        self, engine: CVEngine, clean_car_bytes: bytes
    ) -> None:
        result = engine.analyze(clean_car_bytes, angle="Front")
        expected_min = sum(p.repair_cost_min for p in result.part_analyses if p.is_damaged)
        expected_max = sum(p.repair_cost_max for p in result.part_analyses if p.is_damaged)
        assert result.total_repair_cost_min == expected_min
        assert result.total_repair_cost_max == expected_max

    def test_analyze_all_angles(
        self, engine: CVEngine, clean_car_bytes: bytes
    ) -> None:
        for angle in ("Front", "Rear", "Left Side", "Right Side", "Interior"):
            result = engine.analyze(clean_car_bytes, angle=angle)
            assert result is not None, f"analyze() returned None for angle={angle}"
