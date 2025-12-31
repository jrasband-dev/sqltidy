# SQLTidy Test Suite

Comprehensive test suite for SQLTidy SQL formatter.

## Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── unit/                    # Unit tests for individual components
│   ├── test_tokenizer.py    # Tokenizer tests
│   ├── test_config.py       # Configuration tests
│   └── test_rules.py        # Rule tests
├── integration/             # End-to-end integration tests
│   └── test_formatting.py   # Complete formatting workflows
└── dialects/                # Dialect-specific tests
    ├── test_sqlserver.py    # SQL Server dialect tests
    ├── test_postgresql.py   # PostgreSQL dialect tests
    ├── test_mysql.py        # MySQL dialect tests
    ├── test_oracle.py       # Oracle dialect tests
    └── test_sqlite.py       # SQLite dialect tests
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
# or
python run_tests.py
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/
# or
python run_tests.py unit

# Integration tests only
pytest tests/integration/
# or
python run_tests.py integration

# Dialect tests only
pytest tests/dialects/
# or
python run_tests.py dialects
```

### Run Specific Test Files

```bash
pytest tests/unit/test_tokenizer.py
pytest tests/dialects/test_sqlserver.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/unit/test_tokenizer.py::TestBasicTokenization

# Run a specific test function
pytest tests/unit/test_tokenizer.py::TestBasicTokenization::test_simple_select
```

### Run Tests Matching a Pattern

```bash
# Run all tests with "keyword" in the name
pytest -k keyword

# Run all tests for SQL Server
pytest -k sqlserver
```

### Verbose Output

```bash
pytest -v
# or
python run_tests.py -v
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Run Tests in Parallel (requires pytest-xdist)

```bash
pip install pytest-xdist
pytest -n auto
```

## Test Coverage

Generate test coverage report:

```bash
# HTML report (opens in browser)
pytest --cov=sqltidy --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=sqltidy --cov-report=term

# Both
pytest --cov=sqltidy --cov-report=html --cov-report=term
```

## Writing New Tests

### Using Fixtures

Fixtures are defined in `conftest.py` and automatically available to all tests:

```python
def test_with_fixtures(simple_sql, sqlserver_config):
    """Test using predefined fixtures."""
    result = format_sql(simple_sql, config=sqlserver_config)
    assert result is not None
```

Available fixtures:
- `simple_sql` - Simple SELECT query
- `complex_sql` - Complex query with joins
- `default_config` - Default TidyConfig
- `sqlserver_config` - SQL Server config
- `postgresql_config` - PostgreSQL config
- `mysql_config` - MySQL config
- `oracle_config` - Oracle config
- `sqlite_config` - SQLite config
- `all_dialects` - Parameterized fixture for all dialects
- `dialect_config` - Config for each dialect

### Test Organization

**Unit Tests** (`tests/unit/`)
- Test individual functions/classes in isolation
- Fast execution
- Mock external dependencies
- One assertion per test preferred

**Integration Tests** (`tests/integration/`)
- Test complete workflows
- End-to-end scenarios
- May be slower
- Test interactions between components

**Dialect Tests** (`tests/dialects/`)
- Dialect-specific features
- Keyword/function/data type tests
- Dialect-specific formatting

### Example Test

```python
import pytest
from sqltidy import format_sql
from sqltidy.config import TidyConfig


class TestMyFeature:
    """Test my new feature."""
    
    def test_basic_behavior(self):
        """Test basic behavior of feature."""
        sql = "select id from users"
        config = TidyConfig(dialect='sqlserver')
        result = format_sql(sql, config=config)
        
        assert 'SELECT' in result
    
    @pytest.mark.parametrize("dialect", ['sqlserver', 'postgresql', 'mysql'])
    def test_across_dialects(self, dialect):
        """Test feature works across dialects."""
        config = TidyConfig(dialect=dialect)
        # ... test code
```

## Best Practices

1. **Test names should be descriptive**
   - Good: `test_uppercase_keywords_for_sqlserver`
   - Bad: `test1`

2. **One assertion per test when possible**
   - Makes failures easier to diagnose
   - Tests stay focused

3. **Use fixtures for common setup**
   - Defined in `conftest.py`
   - Reusable across tests

4. **Group related tests in classes**
   - Easier to organize
   - Can share setup/teardown

5. **Mark slow tests**
   ```python
   @pytest.mark.slow
   def test_large_query():
       # ... slow test
   ```

6. **Test edge cases**
   - Empty strings
   - Very long queries
   - Special characters
   - Null values

7. **Use parametrize for similar tests**
   ```python
   @pytest.mark.parametrize("input,expected", [
       ("select", "SELECT"),
       ("from", "FROM"),
   ])
   def test_uppercase(input, expected):
       assert input.upper() == expected
   ```

## Continuous Integration

Tests can be run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=sqltidy --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Tests not found
- Ensure test files start with `test_`
- Ensure test functions start with `test_`
- Ensure test classes start with `Test`
- Check `pytest.ini` configuration

### Import errors
- Ensure sqltidy package is installed: `pip install -e .`
- Check PYTHONPATH includes project root

### Fixture not found
- Check `conftest.py` is present
- Ensure fixture is defined correctly

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain >80% code coverage
4. Update this README if needed

---

**Test Suite Status**: All tests passing ✅  
**Coverage**: Comprehensive unit, integration, and dialect tests  
**Last Updated**: December 2025
