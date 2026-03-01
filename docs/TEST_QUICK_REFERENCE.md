# Testing Quick Reference

## Quick Start

```bash
# Activate your virtual environment
source .venv/bin/activate

# Run all tests
pytest -v

# Or use python -m
python -m pytest -v
```

## Common Commands

### Running Tests

```bash
# Run all tests (verbose)
pytest -v

# Run tests in a specific file
pytest tests/test_image_processor.py

# Run a specific test class
pytest tests/test_image_processor.py::TestCropToFixedRoi

# Run a specific test function
pytest tests/test_image_processor.py::TestCropToFixedRoi::test_crop_rectangle

# Run tests matching a name pattern
pytest -k "crop"  # Runs tests with "crop" in the name
```

### Test Categories (Markers)

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Coverage Reports

```bash
# Show coverage in terminal
pytest --cov=backend --cov-report=term-missing

# Generate HTML coverage report (open htmlcov/index.html in browser)
pytest --cov=backend --cov-report=html

# Both terminal and HTML
pytest --cov=backend --cov-report=term-missing --cov-report=html
```

### Useful Options

```bash
# Stop at first failure
pytest -x

# Run last failed tests only
pytest --lf

# Show print statements (even for passing tests)
pytest -s

# Show extra verbose output
pytest -vv

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## Current Test Coverage

After running `pytest --cov=backend --cov-report=html`, open `htmlcov/index.html` in your browser to see:

- **image_processor.py**: 92% covered ✅
- **notion_client.py**: 93% covered ✅
- **user_manager.py**: 78% covered ✅

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures (test helpers)
├── test_image_processor.py     # Unit tests for fixed-ROI cropping
├── test_user_manager.py        # Unit tests for user management
├── test_notion_client.py       # Unit tests for Notion API (with mocking)
└── test_integration.py         # Integration tests (multiple components)
```

## Adding a New Test

1. Create or open a test file in `tests/` directory
2. Import pytest and the module you're testing
3. Write test functions starting with `test_`
4. Use fixtures from `conftest.py` (like `temp_dir`, `sample_image`)

Example:
```python
import pytest
from my_module import my_function

@pytest.mark.unit
def test_my_function():
    # Arrange
    input_value = 10
    
    # Act
    result = my_function(input_value)
    
    # Assert
    assert result == 20
```

## Debugging Failed Tests

```bash
# Show more context in error messages
pytest -vv

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest --showlocals
```

## Best Practices

✅ **DO:**
- Run tests before committing code
- Write tests for new features
- Keep tests simple and readable
- Use descriptive test names
- Mock external API calls

❌ **DON'T:**
- Commit with failing tests
- Skip writing tests for complex logic
- Make tests depend on each other
- Test external libraries
- Use real API credentials in tests

## Next Steps

1. **Read the full guide**: See `TESTING.md` for detailed explanations
2. **Run tests regularly**: Get in the habit of running `pytest` before commits
3. **Add new tests**: When you add features, add tests too
4. **Check coverage**: Run coverage reports to find untested code

---

**Need Help?**
- Full testing guide: `TESTING.md`
- pytest docs: https://docs.pytest.org/
- Example tests: Look at `tests/test_*.py` files
