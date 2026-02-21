# Valley Teacher Coverage App - Testing Guide

## Test Suite Overview

This comprehensive test suite covers all functionality of the Valley Teacher Coverage App using pytest.

## Test Structure

### **Unit Tests**
- `test_ct_logic.py` - Co-teaching logic scenarios
- `test_schedule_parsing.py` - Schedule file parsing
- `test_coverage_assignment.py` - Coverage calculation logic
- `test_utilities.py` - Utility functions

### **Integration Tests**
- `test_integration.py` - End-to-end workflows

### **Fixtures**
- `fixtures.py` - Test data and helper functions

## Running Tests

### **Install Test Dependencies**
```bash
pip install -r requirements-test.txt
```

### **Run All Tests**
```bash
pytest
```

### **Run Specific Test Categories**
```bash
# Run only CT logic tests
pytest -m ct

# Run only parsing tests
pytest -m parsing

# Run only integration tests
pytest -m integration

# Run performance tests
pytest -m performance
```

### **Run with Coverage**
```bash
pytest --cov=main --cov-report=html
```

### **Run Specific Test Files**
```bash
pytest tests/test_ct_logic.py
pytest tests/test_schedule_parsing.py
```

### **Run Specific Test Methods**
```bash
pytest tests/test_ct_logic.py::TestCTScenarios::test_ct_teacher_present
```

## Test Coverage Areas

### **1. CT Logic Tests** (`test_ct_logic.py`)
- ✅ CT entry detection patterns
- ✅ Name matching (first/last/full names)
- ✅ CT teacher present scenario
- ✅ Both teachers out scenario
- ✅ No CT teacher found scenario
- ✅ Multiple CT teachers per period
- ✅ Split periods with CT
- ✅ Error handling (empty files, invalid paths)

### **2. Schedule Parsing Tests** (`test_schedule_parsing.py`)
- ✅ Excel file parsing
- ✅ CSV file parsing
- ✅ Invalid file handling
- ✅ Name parsing and validation
- ✅ Coverage string parsing
- ✅ Teacher creation and merging
- ✅ Duplicate teacher handling
- ✅ Edge cases (missing columns, malformed data)

### **3. Coverage Assignment Tests** (`test_coverage_assignment.py`)
- ✅ Standard coverage assignment
- ✅ Split period assignment
- ✅ ISS fallback logic
- ✅ Even/odd day logic
- ✅ Duty classification
- ✅ Coverage calculation
- ✅ Coverage tracker updates
- ✅ CT period formatting in output

### **4. Utility Function Tests** (`test_utilities.py`)
- ✅ Ordinal suffix generation
- ✅ Unique and ordered lists
- ✅ Period sorting (regular and split)
- ✅ Edge cases and invalid inputs

### **5. Integration Tests** (`test_integration.py`)
- ✅ Complete Excel workflow
- ✅ Complete CSV workflow
- ✅ CT scenario workflows
- ✅ File format compatibility
- ✅ Performance with large datasets
- ✅ Complex coverage scenarios
- ✅ Error recovery
- ✅ Memory efficiency

## Test Data

### **Fixtures Provide:**
- Sample schedule DataFrames
- Temporary Excel/CSV files
- Teacher objects with various configurations
- Coverage tracker files
- Mock GUI applications

### **Test Scenarios Cover:**
- All CT logic combinations
- File format variations
- Edge cases and error conditions
- Performance scenarios
- Real-world usage patterns

## Expected Test Results

### **Successful Run:**
```
============================= test session starts ==============================
collected 85 tests

tests/test_ct_logic.py::TestCTEntryDetection::test_is_ct_entry[Class CT Smith-True-Standard CT format] PASSED
tests/test_ct_logic.py::TestCTEntryDetection::test_is_ct_entry[Lunch-False-Non-CT entry] PASSED
...
============================== 85 passed in 12.34s ===============================
```

### **Coverage Report:**
- Target: >80% code coverage
- HTML report generated in `htmlcov/`
- Highlights untested code paths

## Continuous Integration

### **GitHub Actions Integration:**
```yaml
- name: Run Tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=main --cov-report=xml
```

### **Pre-commit Hooks:**
```bash
# Run tests before each commit
pytest tests/
```

## Adding New Tests

### **For New Features:**
1. Add test class to appropriate test file
2. Use existing fixtures or create new ones
3. Test both success and failure cases
4. Add appropriate markers (`@pytest.mark.unit`, etc.)

### **Example New Test:**
```python
@pytest.mark.unit
def test_new_feature(self, sample_teachers):
    """Test new feature functionality"""
    result = new_function(sample_teachers)
    assert expected_result in result
```

## Troubleshooting

### **Common Issues:**
1. **Import errors**: Ensure `conftest.py` is in project root
2. **Fixture not found**: Check fixture scope and imports
3. **Temp file cleanup**: Tests should use `yield` for cleanup
4. **Mock objects**: Use `pytest-mock` for GUI components

### **Debugging Failed Tests:**
```bash
# Run with verbose output
pytest -v -s tests/test_failing.py

# Run single test with pdb
pytest tests/test_failing.py::TestClass::test_method --pdb
```

## Performance Considerations

### **Test Optimization:**
- Tests use temporary files that are automatically cleaned up
- Large dataset tests are marked with `@pytest.mark.performance`
- Integration tests use realistic but manageable data sizes

### **Memory Management:**
- Fixtures handle cleanup automatically
- Large files are created in temp directories
- Garbage collection tested in error recovery

This test suite provides comprehensive coverage of all application functionality and ensures reliability across different scenarios and edge cases.
