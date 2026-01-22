"""
Pytest configuration and shared fixtures.

Fixtures are reusable test components that can be injected into test functions.
Think of them as "test setup" that can be shared across multiple tests.
"""
import pytest
import os
import tempfile
import json
import numpy as np
import cv2


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.
    
    This fixture automatically creates and cleans up a temp directory.
    Use it when tests need to write files.
    
    Example:
        def test_something(temp_dir):
            file_path = os.path.join(temp_dir, "test.txt")
            # ... use the temp directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_users():
    """
    Sample user data for testing.
    
    Returns a dictionary of test users with valid structure.
    """
    return {
        "test_user_1": {
            "name": "Test User 1",
            "notion_database_id": "test_db_id_1",
            "notion_token": "test_token_1"
        },
        "test_user_2": {
            "name": "Test User 2",
            "notion_database_id": "test_db_id_2",
            "notion_token": "test_token_2"
        }
    }


@pytest.fixture
def temp_users_file(temp_dir, sample_users):
    """
    Create a temporary users.json file for testing.
    
    Combines temp_dir and sample_users fixtures to create a test users file.
    """
    users_file = os.path.join(temp_dir, "users.json")
    with open(users_file, 'w') as f:
        json.dump(sample_users, f, indent=2)
    return users_file


@pytest.fixture
def sample_image():
    """
    Create a simple test image (100x100 white square).
    
    Returns:
        numpy array representing an image
    """
    # Create a 100x100 white image (BGR format)
    image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    return image


@pytest.fixture
def sample_image_with_aruco():
    """
    Create a test image with ArUco markers at the corners.
    
    This is useful for testing ArUco detection and cropping functions.
    Returns a 400x400 image with markers at corners.
    """
    # Create a white canvas
    image = np.ones((400, 400, 3), dtype=np.uint8) * 255
    
    # Generate ArUco markers (IDs 0-3 for corners)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker_size = 50
    
    # Generate markers for each corner (IDs 0, 1, 2, 3)
    positions = [
        (10, 10),      # Top-left (ID 0)
        (340, 10),     # Top-right (ID 1)
        (10, 340),     # Bottom-left (ID 2)
        (340, 340),    # Bottom-right (ID 3)
    ]
    
    for marker_id, (x, y) in enumerate(positions):
        marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
        # Place marker on image
        image[y:y+marker_size, x:x+marker_size] = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
    
    return image


@pytest.fixture
def temp_image_file(temp_dir, sample_image):
    """
    Create a temporary image file for testing.
    
    Returns:
        Path to the temporary image file
    """
    image_path = os.path.join(temp_dir, "test_image.jpg")
    cv2.imwrite(image_path, sample_image)
    return image_path


@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Set up mock environment variables for testing.
    
    The monkeypatch fixture is provided by pytest and allows
    you to modify environment variables for a test.
    """
    monkeypatch.setenv("SPENCER_NOTION_TOKEN", "mock_spencer_token")
    monkeypatch.setenv("SPENCER_NOTION_DATABASE_ID", "mock_spencer_db")
    monkeypatch.setenv("CELESTE_NOTION_TOKEN", "mock_celeste_token")
    monkeypatch.setenv("CELESTE_NOTION_DATABASE_ID", "mock_celeste_db")
