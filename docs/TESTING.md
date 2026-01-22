# Testing Guide for Notepad Scanner

This guide will help you understand and run the test suite for the notepad scanner project.

## Table of Contents

1. [Setup](#setup)
2. [Running Tests](#running-tests)
3. [Understanding Test Structure](#understanding-test-structure)
4. [Writing New Tests](#writing-new-tests)
5. [Best Practices](#best-practices)

---

## Setup

### Install Test Dependencies

First, install the testing dependencies:

```bash
pip install -r requirements-dev.txt
```

This installs:
- **pytest**: The testing framework
- **pytest-cov**: For code coverage reports
- **pytest-mock**: For creating mock objects
- **pytest-timeout**: For handling long-running tests

### Verify Installation

Check that pytest is installed:

```bash
pytest --version
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_image_processor.py
```

### Run Specific Test Class or Function

```bash
# Run a specific class
pytest tests/test_image_processor.py::TestCalculateMarkerWidth

# Run a specific test function
pytest tests/test_image_processor.py::TestCalculateMarkerWidth::test_single_marker_width
```

### Run Tests by Marker

Tests are organized with markers (defined in `pytest.ini`):

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all tests except slow ones
pytest -m "not slow"
```

### Run with Coverage Report

```bash
# Generate coverage report in terminal
pytest --cov=backend --cov-report=term-missing

# Generate HTML coverage report (open htmlcov/index.html after)
pytest --cov=backend --cov-report=html
```

### Watch Mode (Run Tests on File Change)

Install pytest-watch:
```bash
pip install pytest-watch
```

Then run:
```bash
ptw
```

---

## Understanding Test Structure

### Directory Layout

```
notepad_scanner/
├── tests/                      # All tests go here
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures and configuration
│   ├── test_image_processor.py    # Unit tests for image processing
│   ├── test_user_manager.py       # Unit tests for user management
│   ├── test_notion_client.py      # Unit tests for Notion API
│   └── test_integration.py        # Integration tests
├── pytest.ini                  # Pytest configuration
└── requirements-dev.txt       # Test dependencies
```

### Key Concepts

#### 1. **Test Functions**

Test functions start with `test_` and contain assertions:

```python
def test_something():
    result = my_function(input_value)
    assert result == expected_value
```

#### 2. **Test Classes**

Group related tests together:

```python
class TestMyFeature:
    def test_case_1(self):
        # Test something
        pass
    
    def test_case_2(self):
        # Test something else
        pass
```

#### 3. **Fixtures**

Fixtures are reusable setup code. They're defined in `conftest.py` and can be injected into tests:

```python
@pytest.fixture
def temp_dir():
    """Creates a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_file_operations(temp_dir):
    # temp_dir is automatically provided by pytest
    file_path = os.path.join(temp_dir, "test.txt")
    # ... use temp_dir in your test
```

Available fixtures in this project:
- `temp_dir`: Temporary directory that auto-cleans up
- `sample_users`: Dictionary of test user data
- `temp_users_file`: Temporary users.json file
- `sample_image`: Simple test image (100x100)
- `sample_image_with_aruco`: Test image with ArUco markers
- `temp_image_file`: Temporary image file saved to disk
- `mock_env_vars`: Mock environment variables

#### 4. **Mocking**

Mocking replaces real objects with fake ones for testing. Use it to:
- Avoid calling external APIs
- Simulate error conditions
- Speed up tests

```python
def test_api_call(mocker):
    # Replace requests.post with a mock
    mock_post = mocker.patch('module.requests.post')
    mock_post.return_value.status_code = 200
    
    # Now when code calls requests.post, it gets the mock instead
    result = my_api_function()
    
    # Verify the mock was called
    mock_post.assert_called_once()
```

#### 5. **Markers**

Markers categorize tests:

```python
@pytest.mark.unit
def test_pure_function():
    # Fast, isolated test
    pass

@pytest.mark.integration
def test_workflow():
    # Tests multiple components together
    pass

@pytest.mark.slow
def test_long_operation():
    # Test that takes a long time
    pass
```

---

## Writing New Tests

### Step 1: Decide What to Test

Good candidates for testing:
- ✅ Pure functions (input → output, no side effects)
- ✅ Business logic
- ✅ Edge cases (empty input, invalid data, etc.)
- ✅ Error handling

Less valuable to test:
- ❌ Third-party library code
- ❌ Simple getters/setters
- ❌ Configuration constants

### Step 2: Choose Test Type

**Unit Test**: Test a single function/method in isolation
- Fast (milliseconds)
- No external dependencies
- Use mocking for external calls

**Integration Test**: Test multiple components together
- Slower (may take seconds)
- Tests realistic workflows
- Minimal mocking

### Step 3: Write the Test

Follow the **Arrange-Act-Assert** pattern:

```python
def test_example():
    # ARRANGE: Set up test data and conditions
    input_value = 42
    expected_output = 84
    
    # ACT: Call the function being tested
    result = double(input_value)
    
    # ASSERT: Verify the result
    assert result == expected_output
```

### Step 4: Use Descriptive Names

Good test names describe what they test:

```python
# ❌ Bad
def test_1():
    pass

# ✅ Good
def test_calculate_marker_width_returns_zero_for_empty_list():
    pass

# ✅ Also good (using class grouping)
class TestCalculateMarkerWidth:
    def test_returns_zero_for_empty_list(self):
        pass
```

### Example: Adding a New Test

Let's say you want to test a new function `resize_image`:

```python
# In backend/image_utils.py (your new module)
def resize_image(image, width, height):
    """Resize image to specified dimensions."""
    return cv2.resize(image, (width, height))
```

Create `tests/test_image_utils.py`:

```python
import pytest
import numpy as np
from backend.image_utils import resize_image


@pytest.mark.unit
class TestResizeImage:
    """Tests for resize_image function."""
    
    def test_resize_to_smaller_dimensions(self, sample_image):
        """Test resizing image to smaller size."""
        # Arrange
        original_shape = sample_image.shape  # (100, 100, 3)
        new_width, new_height = 50, 50
        
        # Act
        resized = resize_image(sample_image, new_width, new_height)
        
        # Assert
        assert resized.shape == (50, 50, 3)
        assert resized.shape[0] < original_shape[0]
    
    def test_resize_to_larger_dimensions(self, sample_image):
        """Test resizing image to larger size."""
        resized = resize_image(sample_image, 200, 200)
        assert resized.shape == (200, 200, 3)
    
    def test_resize_maintains_aspect_ratio(self, sample_image):
        """Test that we can create non-square images."""
        resized = resize_image(sample_image, 100, 50)
        assert resized.shape == (50, 100, 3)  # height, width in numpy
```

---

## Best Practices

### ✅ DO

1. **Test behavior, not implementation**
   - Test what the function does, not how it does it
   - This makes tests resilient to refactoring

2. **Keep tests simple and readable**
   - One assertion per test (when practical)
   - Clear test names
   - Minimal setup code

3. **Use fixtures for common setup**
   - Reduces code duplication
   - Makes tests cleaner

4. **Test edge cases**
   - Empty inputs
   - Null/None values
   - Very large values
   - Invalid inputs

5. **Mock external dependencies**
   - API calls
   - Database access
   - File system (when appropriate)

6. **Run tests before committing**
   - Catch bugs early
   - Maintain confidence in your code

### ❌ DON'T

1. **Don't test external libraries**
   - Trust that numpy, cv2, etc. work correctly
   - Test your code that uses them

2. **Don't write tests that depend on each other**
   - Each test should be independent
   - Order shouldn't matter

3. **Don't use real credentials in tests**
   - Use mock tokens/keys
   - Never commit real API keys

4. **Don't make tests too complex**
   - If a test is hard to understand, simplify it
   - Complex tests are hard to maintain

---

## Common Test Patterns

### Testing Exceptions

```python
def test_function_raises_error_on_invalid_input():
    with pytest.raises(ValueError, match="Expected error message"):
        my_function(invalid_input)
```

### Parametrized Tests (Testing Multiple Inputs)

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

### Testing File Operations

```python
def test_save_file(temp_dir):
    file_path = os.path.join(temp_dir, "test.txt")
    
    # Write file
    save_data(file_path, "test content")
    
    # Verify it was created
    assert os.path.exists(file_path)
    
    # Verify contents
    with open(file_path) as f:
        assert f.read() == "test content"
```

### Mocking Environment Variables

```python
def test_with_env_var(monkeypatch):
    monkeypatch.setenv("MY_VAR", "test_value")
    
    # Your code that reads MY_VAR
    result = function_that_reads_env()
    
    assert result == "test_value"
```

---

## Debugging Failed Tests

### 1. Read the Error Message

Pytest provides detailed error messages:

```
FAILED tests/test_example.py::test_something - assert 5 == 6
```

### 2. Run with More Verbosity

```bash
pytest -vv
```

### 3. Use Print Statements

```python
def test_something():
    result = my_function()
    print(f"Result: {result}")  # Will show if test fails
    assert result == expected
```

### 4. Run in Debug Mode

```bash
pytest --pdb
```

This drops into Python debugger on failure.

### 5. Run Only Failing Tests

```bash
pytest --lf  # Last failed
pytest --ff  # Failed first, then rest
```

---

## Next Steps

1. **Run the existing tests**: `pytest -v`
2. **Add coverage to see what's tested**: `pytest --cov=backend --cov-report=html`
3. **Try writing a simple test** for a new function
4. **Explore pytest documentation**: https://docs.pytest.org/

## Questions?

- Check pytest docs: https://docs.pytest.org/
- Look at existing tests for examples
- Remember: start simple, add complexity as needed

Happy testing! 🧪
