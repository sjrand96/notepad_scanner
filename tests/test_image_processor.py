"""
Unit tests for image_processor module.

Tests focus on fixed-ROI cropping (crop_to_fixed_roi).
"""
import pytest
import numpy as np
from backend.image_processor import crop_to_fixed_roi


@pytest.mark.unit
class TestCropToFixedRoi:
    """Tests for crop_to_fixed_roi function."""

    def test_full_frame_when_roi_zero(self, sample_image):
        """When ROI width/height are 0, use full frame (from roi_x, roi_y to end)."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:] = 42
        cropped = crop_to_fixed_roi(img, 0, 0, 0, 0)
        assert cropped is not None
        assert cropped.shape == (100, 100, 3)
        assert cropped[0, 0, 0] == 42

    def test_crop_rectangle(self, sample_image):
        """Crop to a valid rectangle."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[10:30, 20:60] = 100
        cropped = crop_to_fixed_roi(img, 20, 10, 40, 20)
        assert cropped is not None
        assert cropped.shape == (20, 40, 3)
        assert cropped[0, 0, 0] == 100

    def test_roi_clamped_to_bounds(self):
        """ROI that extends past image is clamped."""
        img = np.ones((50, 50, 3), dtype=np.uint8) * 200
        cropped = crop_to_fixed_roi(img, 10, 10, 100, 100)
        assert cropped is not None
        assert cropped.shape == (40, 40, 3)

    def test_none_input(self):
        """None image returns None."""
        assert crop_to_fixed_roi(None, 0, 0, 50, 50) is None

    def test_zero_height_image_returns_none(self):
        """Zero-height image returns None."""
        img = np.zeros((0, 10, 3), dtype=np.uint8)
        cropped = crop_to_fixed_roi(img, 0, 0, 5, 5)
        assert cropped is None

    def test_roi_zero_size_after_clamp_returns_none(self):
        """ROI entirely outside image can yield no crop."""
        img = np.ones((20, 20, 3), dtype=np.uint8)
        cropped = crop_to_fixed_roi(img, 30, 30, 10, 10)
        assert cropped is None
