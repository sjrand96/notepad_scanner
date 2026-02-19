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
            "notion_token": "test_token_1",
            "notion_token_env_var_name": "TEST_USER_1_NOTION_TOKEN",
        },
        "test_user_2": {
            "name": "Test User 2",
            "notion_database_id": "test_db_id_2",
            "notion_token": "test_token_2",
            "notion_token_env_var_name": "TEST_USER_2_NOTION_TOKEN",
        },
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
