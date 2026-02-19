"""
TEMPLATE: Use this as a starting point for writing your own tests.

This file shows common patterns for testing in this project.
Copy the pattern that fits your needs and adapt it.
"""
import pytest


# ============================================================================
# PATTERN 1: Testing a Pure Function (No External Dependencies)
# ============================================================================

@pytest.mark.unit
def test_simple_function():
    """
    Test a simple function with a clear input → output relationship.
    
    Use the Arrange-Act-Assert pattern:
    - Arrange: Set up test data
    - Act: Call the function
    - Assert: Check the result
    """
    # Arrange
    input_value = 5
    expected_output = 10
    
    # Act
    # result = double(input_value)  # Replace with your function
    result = input_value * 2  # Placeholder
    
    # Assert
    assert result == expected_output


# ============================================================================
# PATTERN 2: Testing Multiple Cases (Parametrized Tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (5, 10),
    (0, 0),
    (-3, -6),
])
def test_function_with_multiple_inputs(input_val, expected):
    """
    Test the same function with different inputs.
    
    This runs the test 4 times, once for each parameter set.
    Great for testing edge cases!
    """
    # Act
    result = input_val * 2  # Replace with your function
    
    # Assert
    assert result == expected


# ============================================================================
# PATTERN 3: Testing with Test Data from Fixtures
# ============================================================================

@pytest.mark.unit
def test_with_fixture(sample_image):
    """
    Test using a fixture from conftest.py.
    
    Available fixtures:
    - temp_dir: Temporary directory
    - sample_image: 100x100 test image
    - temp_image_file: Saved image file
    - temp_users_file: Temporary users.json
    """
    # sample_image is automatically provided by pytest
    height, width, channels = sample_image.shape
    
    assert height == 100
    assert width == 100
    assert channels == 3


# ============================================================================
# PATTERN 4: Testing File Operations
# ============================================================================

@pytest.mark.unit
def test_file_operations(temp_dir):
    """
    Test code that reads/writes files.
    
    temp_dir is automatically cleaned up after the test.
    """
    import os
    
    # Create a test file
    test_file = os.path.join(temp_dir, "test.txt")
    
    # Write to file
    with open(test_file, 'w') as f:
        f.write("test content")
    
    # Verify file exists
    assert os.path.exists(test_file)
    
    # Verify content
    with open(test_file, 'r') as f:
        content = f.read()
    assert content == "test content"


# ============================================================================
# PATTERN 5: Testing Exceptions
# ============================================================================

@pytest.mark.unit
def test_function_raises_error():
    """
    Test that a function raises the expected exception.
    """
    def function_that_should_fail(value):
        if value < 0:
            raise ValueError("Value must be positive")
        return value * 2
    
    # Test that it raises ValueError
    with pytest.raises(ValueError, match="must be positive"):
        function_that_should_fail(-1)
    
    # Test that positive values work fine
    result = function_that_should_fail(5)
    assert result == 10


# ============================================================================
# PATTERN 6: Testing with Mocked External Calls
# ============================================================================

@pytest.mark.unit
def test_with_mocking(mocker):
    """
    Test code that makes external calls (API, database, etc.).
    
    Use mocking to avoid real external calls in tests.
    """
    # Mock a function that makes an API call
    mock_api_call = mocker.patch('requests.get')
    
    # Configure what the mock should return
    mock_api_call.return_value.status_code = 200
    mock_api_call.return_value.json.return_value = {"result": "success"}
    
    # Now when code calls requests.get, it gets the mock instead
    import requests
    response = requests.get("http://example.com")
    
    # Verify the mock behavior
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    
    # Verify the mock was called
    mock_api_call.assert_called_once()


# ============================================================================
# PATTERN 7: Testing with Environment Variables
# ============================================================================

@pytest.mark.unit
def test_with_env_vars(monkeypatch):
    """
    Test code that reads environment variables.
    
    monkeypatch lets you set env vars for the test.
    """
    # Set an environment variable for this test only
    monkeypatch.setenv("MY_CONFIG_VAR", "test_value")
    
    import os
    result = os.getenv("MY_CONFIG_VAR")
    
    assert result == "test_value"


# ============================================================================
# PATTERN 8: Organizing Tests in Classes
# ============================================================================

@pytest.mark.unit
class TestMyFeature:
    """
    Group related tests together in a class.
    
    Class names must start with "Test".
    Method names must start with "test_".
    """
    
    def test_basic_case(self):
        """Test the basic/happy path."""
        result = 2 + 2
        assert result == 4
    
    def test_edge_case(self):
        """Test an edge case."""
        result = 0 + 0
        assert result == 0
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ZeroDivisionError):
            _ = 1 / 0


# ============================================================================
# PATTERN 9: Integration Test (Multiple Components)
# ============================================================================

@pytest.mark.integration
def test_complete_workflow(temp_dir):
    """
    Integration test that exercises multiple components together.
    
    These are slower but test realistic scenarios.
    """
    import os
    import json
    
    # Step 1: Create some data
    data = {"name": "test", "value": 123}
    file_path = os.path.join(temp_dir, "data.json")
    
    # Step 2: Save it
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    # Step 3: Load it back
    with open(file_path, 'r') as f:
        loaded_data = json.load(f)
    
    # Step 4: Verify the complete workflow
    assert loaded_data == data


# ============================================================================
# HOW TO USE THIS TEMPLATE
# ============================================================================

"""
1. Copy the pattern that matches your testing needs
2. Replace placeholder code with your actual function calls
3. Update the docstring to describe what you're testing
4. Run the test: pytest tests/test_example_template.py -v
5. Once it passes, move it to the appropriate test file

TIPS:
- Start simple - test one thing at a time
- Use descriptive test names (test_what_youre_testing)
- Include docstrings to explain why the test exists
- Test both success cases AND error cases
- Use fixtures to reduce setup code
- Mock external dependencies (APIs, databases, etc.)

RUNNING JUST THIS FILE:
pytest tests/test_example_template.py -v
"""
