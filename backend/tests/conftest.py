"""
AutoWorth AI — CV Tests conftest

Injects the cv2 mock into sys.path BEFORE any test module imports cv2,
so the CV engine unit tests run without the OpenCV binary wheel installed.
The mock is skipped if real cv2 is already available.
"""

from __future__ import annotations

import sys
import pathlib

# Only inject mock if cv2 is not already installed
try:
    import cv2  # noqa: F401
except ImportError:
    mock_dir = pathlib.Path(__file__).parent / "cv2_mock"
    sys.path.insert(0, str(mock_dir))
    print(f"\n[conftest] cv2 not found — injecting mock from {mock_dir}")
