"""
cv2 mock module for unit testing the CV engine without OpenCV installed.

Provides numpy-based stubs for the cv2 functions used by CVEngine:
  - imdecode / imencode
  - cvtColor (BGR↔GRAY, BGR↔HSV, RGB→BGR)
  - GaussianBlur
  - Canny
  - rectangle / putText / getTextSize / addWeighted
  - IMREAD_COLOR, FONT_HERSHEY_SIMPLEX, LINE_AA colour constants
"""

from __future__ import annotations
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────
IMREAD_COLOR       = 1
FONT_HERSHEY_SIMPLEX = 0
LINE_AA            = 16
COLOR_BGR2GRAY     = 6
COLOR_BGR2HSV      = 40
COLOR_RGB2BGR      = 4

__version__ = "4.10.0.84-mock"


# ── Core image I/O ────────────────────────────────────────────────────────────

def imdecode(buf: np.ndarray, flags: int) -> np.ndarray | None:
    """Decode image bytes via Pillow (already installed)."""
    try:
        import io
        from PIL import Image
        data = bytes(buf.tobytes())
        pil = Image.open(io.BytesIO(data)).convert("RGB")
        arr = np.array(pil, dtype=np.uint8)
        # Convert RGB → BGR
        return arr[:, :, ::-1].copy()
    except Exception:
        return None


def imencode(ext: str, img: np.ndarray, params=None):
    """Encode ndarray to image bytes via Pillow."""
    try:
        import io
        from PIL import Image
        # BGR → RGB
        rgb = img[:, :, ::-1].copy()
        pil = Image.fromarray(rgb.astype(np.uint8))
        buf = io.BytesIO()
        fmt = "PNG" if "png" in ext.lower() else "JPEG"
        pil.save(buf, format=fmt)
        data = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        return True, data
    except Exception:
        return False, np.array([], dtype=np.uint8)


# ── Colour conversion ─────────────────────────────────────────────────────────

def cvtColor(src: np.ndarray, code: int) -> np.ndarray:
    if code == COLOR_BGR2GRAY:
        # Standard luminance: 0.299R + 0.587G + 0.114B  (src is BGR)
        b, g, r = src[:,:,0].astype(float), src[:,:,1].astype(float), src[:,:,2].astype(float)
        return (0.114*b + 0.587*g + 0.299*r).astype(np.uint8)
    elif code == COLOR_BGR2HSV:
        # Approximate: return a 3-channel array with realistic saturation
        # For testing purposes we only need shape (h,w,3) with channel 1 = saturation
        result = np.zeros_like(src)
        # Saturation approximation: colour distance from grey
        grey = cvtColor(src, COLOR_BGR2GRAY)
        for c in range(3):
            result[:,:,c] = np.abs(src[:,:,c].astype(int) - grey.astype(int)).clip(0,255).astype(np.uint8)
        return result
    elif code == COLOR_RGB2BGR:
        return src[:, :, ::-1].copy()
    else:
        return src.copy()


# ── Filters ───────────────────────────────────────────────────────────────────

def GaussianBlur(src: np.ndarray, ksize: tuple, sigmaX: float, **kwargs) -> np.ndarray:
    """Simple box blur approximation."""
    k = max(ksize[0], 1)
    if k <= 1:
        return src.copy()
    result = src.copy().astype(float)
    # Simple uniform average over k×k neighbourhood
    from numpy.lib.stride_tricks import sliding_window_view
    pad = k // 2
    padded = np.pad(src.astype(float), pad, mode='edge')
    if padded.ndim == 3:
        out = np.zeros_like(src, dtype=float)
        for c in range(src.shape[2]):
            p = np.pad(src[:,:,c].astype(float), pad, mode='edge')
            windows = sliding_window_view(p, (k,k))
            out[:,:,c] = windows.mean(axis=(-2,-1))
        return out.astype(np.uint8)
    else:
        padded = np.pad(src.astype(float), pad, mode='edge')
        windows = sliding_window_view(padded, (k,k))
        return windows.mean(axis=(-2,-1)).astype(np.uint8)


def Canny(src: np.ndarray, threshold1: float, threshold2: float, **kwargs) -> np.ndarray:
    """Approximate edge detection via gradient magnitude."""
    src_f = src.astype(float)
    # Sobel-like gradient
    gx = np.zeros_like(src_f)
    gy = np.zeros_like(src_f)
    gx[:, 1:] = np.abs(np.diff(src_f, axis=1))
    gy[1:, :] = np.abs(np.diff(src_f, axis=0))
    mag = np.sqrt(gx**2 + gy**2)
    edges = (mag > threshold1).astype(np.uint8) * 255
    return edges


# ── Drawing ───────────────────────────────────────────────────────────────────

def rectangle(img: np.ndarray, pt1: tuple, pt2: tuple, color: tuple, thickness: int) -> None:
    """Draw rectangle in-place (simplified — no clipping)."""
    x1, y1 = max(0, pt1[0]), max(0, pt1[1])
    x2, y2 = min(img.shape[1]-1, pt2[0]), min(img.shape[0]-1, pt2[1])
    if thickness < 0:
        # Filled
        img[y1:y2, x1:x2] = color[:3] if len(color) >= 3 else color
    else:
        t = max(1, thickness)
        img[y1:y1+t, x1:x2] = color[:3]
        img[y2-t:y2, x1:x2] = color[:3]
        img[y1:y2, x1:x1+t] = color[:3]
        img[y1:y2, x2-t:x2] = color[:3]


def putText(img, text, org, fontFace, fontScale, color, thickness=1, lineType=LINE_AA):
    """No-op stub — text rendering not needed for logic tests."""
    pass


def getTextSize(text: str, fontFace, fontScale: float, thickness: int) -> tuple:
    """Return approximate text bounding box."""
    char_w = int(8 * fontScale)
    char_h = int(12 * fontScale)
    return (len(text) * char_w, char_h), 0


def addWeighted(src1: np.ndarray, alpha: float, src2: np.ndarray, beta: float, gamma: float) -> np.ndarray:
    result = (src1.astype(float) * alpha + src2.astype(float) * beta + gamma)
    return result.clip(0, 255).astype(np.uint8)
