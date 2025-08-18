# SI Component Management System - Test Suite

Comprehensive testing framework for the SI Component Management System.

## Directory Structure

```
tests/
├── README.md                          # This file
├── __init__.py                        # Test module initialization
├── test_framework.py                  # Base testing framework and utilities
├── run_all_tests.py                  # Comprehensive test runner
├── test_si_session.py                # Tests for SI session management
├── test_schema_fetcher.py             # Tests for schema template fetcher
├── test_changeset_extractor.py        # Tests for changeset component extractor
├── test_component_config_system.py    # Tests for component configuration system
└── test_results/                     # Test results and generated files
    ├── comprehensive_test_report_*.json # Consolidated test reports
    ├── *_test_results.json            # Individual test suite results
    ├── schema_templates/               # Test schema templates
    ├── extracted_components/           # Test component extractions
    └── test_configs/                  # Test configuration files
```

## Running Tests

### Prerequisites
Ensure environment variables are set:
```bash
export SI_WORKSPACE_ID='your-workspace-id'
export SI_API_TOKEN='your-api-token'
export SI_HOST='https://api.systeminit.com'  # optional
```

### Run All Tests (Recommended)
```bash
cd tests
python run_all_tests.py
```

### Run Individual Test Suites
```bash
# SI Session tests
python test_si_session.py

# Schema Fetcher tests
python test_schema_fetcher.py

# Changeset Extractor tests
python test_changeset_extractor.py

# Component Config System tests
python test_component_config_system.py
```

## Test Suites Overview

### 1. SI Session Tests (`test_si_session.py`)
Tests core SI API functionality:
- ✅ Environment variable validation
- ✅ Session creation and authentication
- ✅ Changeset retrieval
- ✅ Component listing
- ✅ Schema discovery

### 2. Schema Fetcher Tests (`test_schema_fetcher.py`)
Tests schema template generation:
- ✅ Basic schema template fetching
- ✅ "Needed to deploy" section generation
- ✅ Complete example section generation
- ✅ Invalid schema handling
- ✅ AWS-specific requirements detection

### 3. Changeset Extractor Tests (`test_changeset_extractor.py`)
Tests component extraction and transformation:
- ✅ Basic component extraction from changesets
- ✅ Template format transformation
- ✅ Reference examples generation
- ✅ Schema-specific reference patterns
- ✅ Extraction summary generation

### 4. Component Config System Tests (`test_component_config_system.py`)
Tests configuration management:
- ✅ Config manager initialization
- ✅ Configuration loading from files
- ✅ Configuration validation
- ✅ Create component request format conversion
- ✅ ComponentConfig dataclass structure

## Test Framework

### TestFramework Class
Base framework providing:
- Test execution and timing
- Result collection and aggregation
- JSON report generation
- Console output formatting
- Error handling and traceback capture

### Test Result Structure
Each test produces a `TestResult` with:
- `test_name`: Descriptive test name
- `feature`: Feature being tested
- `status`: "PASS", "FAIL", "SKIP", or "ERROR"
- `duration`: Execution time in seconds
- `message`: Success/failure message
- `error_details`: Full traceback for errors
- `output_data`: Test-specific output data

### Assertion Helpers
- `assert_equals(actual, expected, message="")`
- `assert_true(condition, message="")`
- `assert_not_none(value, message="")`
- `assert_contains(container, item, message="")`
- `assert_file_exists(filepath, message="")`

## Test Results Analysis

### Comprehensive Report Format
The consolidated test report includes:

```json
{
  "test_run_info": {
    "timestamp": "2025-08-18T15:30:00.123456",
    "start_time": "2025-08-18T15:29:00.000000",
    "end_time": "2025-08-18T15:30:00.123456",
    "total_duration": 60.12,
    "environment": { /* system info */ }
  },
  "overall_summary": {
    "total_test_suites": 4,
    "total_tests": 20,
    "passed": 18,
    "failed": 1,
    "errors": 1,
    "skipped": 0,
    "success_rate": 90.0
  },
  "suite_results": { /* per-suite breakdown */ },
  "detailed_results": [ /* individual test results */ ]
}
```

### Success Rate Interpretation
- **95-100%**: 🎉 EXCELLENT - All systems functioning properly
- **85-94%**: 👍 GOOD - Most features working, minor issues
- **70-84%**: ⚠️ NEEDS ATTENTION - Several issues to address
- **<70%**: 🚨 CRITICAL - Major issues, system may be unstable

## Test Coverage

### Core Functionality Coverage
- **Authentication & Session Management**: Complete
- **Schema Operations**: Complete
- **Component Operations**: Complete
- **Configuration Management**: Complete
- **File I/O Operations**: Complete
- **API Error Handling**: Complete

### Edge Cases Coverage
- **Invalid inputs**: Schema names, component IDs, file paths
- **Missing dependencies**: Environment variables, files, components
- **Network issues**: API timeouts, authentication failures
- **Data format issues**: Invalid JSON, missing fields

### Performance Testing
- **Large schema handling**: Multi-page results, complex schemas
- **Bulk operations**: Multiple component extraction/creation
- **Resource cleanup**: Temporary files, test data

## Troubleshooting Test Issues

### Common Test Failures

**Authentication Errors:**
- Verify SI_WORKSPACE_ID and SI_API_TOKEN are set correctly
- Check token has appropriate permissions
- Ensure workspace exists and is accessible

**Schema Not Found:**
- Verify test schemas exist in your workspace
- Check schema name spelling and case sensitivity
- Ensure schemas are installed and available

**File System Issues:**
- Check write permissions to test_results directory
- Ensure sufficient disk space for test files
- Verify test files are properly cleaned up

**Network/API Issues:**
- Check internet connectivity to SI API
- Verify SI_HOST setting (defaults to api.systeminit.com)
- Check for rate limiting or temporary API issues

### Debug Mode
Enable detailed logging for debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Test Data Cleanup
If tests leave behind data:
```bash
# Clean test results
rm -rf tests/test_results/*

# Clean temporary test files
find tests/ -name "*.tmp" -delete
find tests/ -name "*_test.*" -delete
```

## Adding New Tests

### Creating a New Test Suite
1. Create `test_your_feature.py` in the tests directory
2. Import the test framework: `from test_framework import TestFramework`
3. Create test class with methods for each test case
4. Use assertion helpers for validation
5. Add to `run_all_tests.py` test_suites list

### Test Method Pattern
```python
def test_your_functionality(self):
    """Test description"""
    try:
        # Arrange
        setup_data = self.setup_test_data()
        
        # Act
        result = self.function_under_test(setup_data)
        
        # Assert
        assert_not_none(result, "Result should not be None")
        assert_true(result["success"], "Operation should succeed")
        
        return {
            "success": True,
            "result_data": result,
            "additional_info": "test-specific data"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Best Practices
- Write descriptive test names and docstrings
- Test both success and failure scenarios
- Include edge cases and boundary conditions
- Clean up test data and temporary files
- Return structured result data for analysis
- Use assertion helpers for consistent error messages

## Continuous Integration

### Integration with CI/CD
The test suite is designed for CI/CD integration:
- Returns appropriate exit codes (0 for success, 1 for failure)
- Generates machine-readable JSON reports
- Supports headless execution
- Minimal external dependencies

### Example CI Configuration
```yaml
# .github/workflows/tests.yml
name: SI Component Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        env:
          SI_WORKSPACE_ID: ${{ secrets.SI_WORKSPACE_ID }}
          SI_API_TOKEN: ${{ secrets.SI_API_TOKEN }}
        run: cd tests && python run_all_tests.py
```

---

**Happy Testing!** 🧪✨