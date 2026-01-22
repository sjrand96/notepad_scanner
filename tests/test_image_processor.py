"""
Unit tests for image_processor module.

These tests focus on isolated functions that perform image processing.
We use pytest markers to categorize tests (@pytest.mark.unit).
"""
import pytest
import numpy as np
import cv2
from backend.image_processor import (
    calculate_marker_width,
    detect_aruco_live,
    detect_aruco_detailed,
    crop_to_aruco_boundaries
)


@pytest.mark.unit
class TestCalculateMarkerWidth:
    """Tests for calculate_marker_width function."""
    
    def test_single_marker_width(self):
        """Test width calculation for a single marker."""
        # Create a simple square marker corners (50x50 pixels)
        corners = [
            np.array([[
                [0, 0],
                [50, 0],
                [50, 50],
                [0, 50]
            ]], dtype=np.float32)
        ]
        
        width = calculate_marker_width(corners)
        
        # Should return approximately 50 pixels
        assert 49 <= width <= 51, f"Expected width ~50, got {width}"
    
    def test_multiple_markers_average(self):
        """Test that function averages width across multiple markers."""
        corners = [
            np.array([[[0, 0], [50, 0], [50, 50], [0, 50]]], dtype=np.float32),
            np.array([[[0, 0], [60, 0], [60, 60], [0, 60]]], dtype=np.float32),
        ]
        
        width = calculate_marker_width(corners)
        
        # Should average to approximately 55
        assert 53 <= width <= 57, f"Expected width ~55, got {width}"
    
    def test_empty_corners(self):
        """Test that function handles empty input gracefully."""
        corners = []
        width = calculate_marker_width(corners)
        assert width == 0, "Empty corners should return 0"


@pytest.mark.unit
class TestArucoDetection:
    """Tests for ArUco marker detection functions."""
    
    @pytest.fixture
    def aruco_setup(self):
        """Setup ArUco dictionary and parameters for tests."""
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        try:
            aruco_params = cv2.aruco.DetectorParameters()
        except AttributeError:
            aruco_params = cv2.aruco.DetectorParameters_create()
        return aruco_dict, aruco_params
    
    def test_detect_no_markers(self, sample_image, aruco_setup):
        """Test detection on image without markers."""
        aruco_dict, aruco_params = aruco_setup
        
        corners, ids, annotated = detect_aruco_live(
            sample_image, aruco_dict, aruco_params
        )
        
        assert ids is None, "Should detect no markers in plain image"
        assert annotated is not None, "Should still return annotated frame"
    
    def test_detect_with_markers(self, sample_image_with_aruco, aruco_setup):
        """Test detection on image with ArUco markers."""
        aruco_dict, aruco_params = aruco_setup
        
        corners, ids, annotated = detect_aruco_live(
            sample_image_with_aruco, aruco_dict, aruco_params
        )
        
        assert ids is not None, "Should detect markers"
        assert len(ids) == 4, f"Should detect 4 markers, found {len(ids)}"
        assert annotated is not None, "Should return annotated frame"
    
    def test_detect_aruco_detailed(self, sample_image_with_aruco, aruco_setup):
        """Test detailed detection returns all expected outputs."""
        aruco_dict, aruco_params = aruco_setup
        
        corners, ids, labeled_image, all_corners = detect_aruco_detailed(
            sample_image_with_aruco, aruco_dict, aruco_params
        )
        
        assert ids is not None, "Should detect markers"
        assert len(ids) == 4, "Should detect 4 markers"
        assert labeled_image is not None, "Should return labeled image"
        assert len(all_corners) == 4, "Should return all corner lists"


@pytest.mark.unit
class TestCropToArucoBoundaries:
    """Tests for crop_to_aruco_boundaries function."""
    
    @pytest.fixture
    def aruco_setup(self):
        """Setup ArUco dictionary and parameters."""
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        try:
            aruco_params = cv2.aruco.DetectorParameters()
        except AttributeError:
            aruco_params = cv2.aruco.DetectorParameters_create()
        return aruco_dict, aruco_params
    
    def test_crop_with_four_markers(self, sample_image_with_aruco, aruco_setup):
        """Test cropping with all four required markers."""
        aruco_dict, aruco_params = aruco_setup
        
        # Detect markers
        corners, ids, _, _ = detect_aruco_detailed(
            sample_image_with_aruco, aruco_dict, aruco_params
        )
        
        # Crop with no margin
        cropped = crop_to_aruco_boundaries(
            sample_image_with_aruco, corners, ids, margin_factor=0
        )
        
        assert cropped is not None, "Should successfully crop image"
        assert cropped.size > 0, "Cropped image should not be empty"
        # Cropped image should be smaller than original
        assert cropped.shape[0] < sample_image_with_aruco.shape[0]
        assert cropped.shape[1] < sample_image_with_aruco.shape[1]
    
    def test_crop_with_missing_markers(self, sample_image_with_aruco, aruco_setup):
        """Test that cropping fails gracefully when markers are missing."""
        # Manually create incomplete marker data (only 2 markers instead of 4)
        corners = [np.array([[[0, 0], [50, 0], [50, 50], [0, 50]]], dtype=np.float32)]
        ids = np.array([0])  # Only one marker
        
        cropped = crop_to_aruco_boundaries(
            sample_image_with_aruco, corners, ids, margin_factor=0
        )
        
        assert cropped is None, "Should return None when < 4 markers present"
    
    def test_crop_with_none_inputs(self, sample_image_with_aruco):
        """Test that function handles None inputs gracefully."""
        cropped = crop_to_aruco_boundaries(
            sample_image_with_aruco, None, None, margin_factor=0
        )
        assert cropped is None, "Should return None for None inputs"
    
    def test_crop_with_margin(self, sample_image_with_aruco, aruco_setup):
        """Test cropping with margin factor."""
        aruco_dict, aruco_params = aruco_setup
        
        corners, ids, _, _ = detect_aruco_detailed(
            sample_image_with_aruco, aruco_dict, aruco_params
        )
        
        # Crop with positive margin (should make image larger)
        cropped_with_margin = crop_to_aruco_boundaries(
            sample_image_with_aruco, corners, ids, margin_factor=0.2
        )
        
        # Crop with no margin
        cropped_no_margin = crop_to_aruco_boundaries(
            sample_image_with_aruco, corners, ids, margin_factor=0
        )
        
        assert cropped_with_margin is not None
        assert cropped_no_margin is not None
        
        # Image with margin should be larger
        assert cropped_with_margin.shape[0] >= cropped_no_margin.shape[0]
        assert cropped_with_margin.shape[1] >= cropped_no_margin.shape[1]


# ============================================================================
# Debug/Utility Tests
# ============================================================================

@pytest.mark.unit
def test_visualize_fixture(sample_image_with_aruco):
    """
    Debug test to visualize what the sample_image_with_aruco fixture creates.
    
    This test is useful for understanding the test fixtures.
    The generated image is saved to debug_fixture_image.jpg in the project root.
    """
    import cv2
    
    print(f"Image shape: {sample_image_with_aruco.shape}")
    print(f"Image dtype: {sample_image_with_aruco.dtype}")
    
    # Save it to see what it looks like
    cv2.imwrite("debug_fixture_image.jpg", sample_image_with_aruco)
    
    assert sample_image_with_aruco.shape == (400, 400, 3)
