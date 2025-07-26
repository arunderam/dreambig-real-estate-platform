# Testing Guide - DreamBig Real Estate Platform

This document provides comprehensive information about testing the DreamBig Real Estate Platform.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Writing Tests](#writing-tests)
6. [Coverage Reports](#coverage-reports)
7. [Continuous Integration](#continuous-integration)
8. [Troubleshooting](#troubleshooting)

## Overview

The DreamBig platform uses a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API endpoints and component interactions
- **Performance Tests**: Test system performance under load
- **Security Tests**: Test security measures and vulnerability prevention

### Testing Framework

- **pytest**: Primary testing framework
- **pytest-asyncio**: For testing async code
- **pytest-cov**: For coverage reporting
- **pytest-xdist**: For parallel test execution
- **httpx**: For HTTP client testing
- **factory-boy**: For test data generation

## Test Structure

```
app/tests/
├── conftest.py              # Test configuration and fixtures
├── test_models.py           # Database model tests
├── test_crud.py             # CRUD operation tests
├── test_business_rules.py   # Business logic tests
├── test_api_auth.py         # Authentication API tests
├── test_api_properties.py   # Properties API tests
├── test_performance.py      # Performance tests
└── test_security.py         # Security tests
```

### Key Files

- **conftest.py**: Contains shared fixtures and test configuration
- **pytest.ini**: Pytest configuration and markers
- **run_tests.py**: Custom test runner script
- **.github/workflows/tests.yml**: CI/CD pipeline configuration

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type performance
python run_tests.py --type security

# Run with coverage
python run_tests.py --type unit --coverage

# Run with parallel execution
python run_tests.py --type all --parallel 4

# Run specific test file
python run_tests.py --file test_models.py

# Run tests matching pattern
python run_tests.py --function test_user_creation
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/test_models.py

# Run specific test function
pytest app/tests/test_models.py::TestUserModel::test_user_creation

# Run with coverage
pytest --cov=app --cov-report=html

# Run with parallel execution
pytest -n auto

# Run with specific markers
pytest -m "unit and not slow"
```

### Environment Setup

Before running tests, ensure you have:

1. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables set** (optional, defaults provided):
   ```bash
   export TESTING=true
   export DATABASE_URL=sqlite:///./test.db
   export SECRET_KEY=test_secret_key
   ```

## Test Categories

### Unit Tests

Test individual components in isolation:

- **Models** (`test_models.py`): Database model validation and relationships
- **CRUD** (`test_crud.py`): Database operations and queries
- **Business Rules** (`test_business_rules.py`): Business logic and calculations

**Markers**: `@pytest.mark.unit`

### Integration Tests

Test API endpoints and component interactions:

- **Authentication** (`test_api_auth.py`): User registration, login, profile management
- **Properties** (`test_api_properties.py`): Property CRUD, search, file uploads

**Markers**: `@pytest.mark.integration`

### Performance Tests

Test system performance under various loads:

- **Database Performance**: Bulk operations, query optimization
- **API Performance**: Response times, concurrent requests
- **Business Rules Performance**: Calculation speed, memory usage

**Markers**: `@pytest.mark.performance`, `@pytest.mark.slow`

### Security Tests

Test security measures and vulnerability prevention:

- **Authentication Security**: Token validation, session management
- **Authorization**: Role-based access control, data isolation
- **Input Validation**: SQL injection, XSS prevention
- **Rate Limiting**: API throttling, brute force protection

**Markers**: `@pytest.mark.security`

## Writing Tests

### Test Structure

```python
import pytest
from app.tests.conftest import assert_response_success, assert_response_error

class TestFeatureName:
    """Test feature description."""
    
    def test_positive_case(self, db_session, test_user):
        """Test successful operation."""
        # Arrange
        data = {"key": "value"}
        
        # Act
        result = some_function(db_session, data)
        
        # Assert
        assert result is not None
        assert result.property == expected_value
    
    def test_negative_case(self, db_session):
        """Test error handling."""
        # Test with invalid data
        with pytest.raises(ValueError):
            some_function(db_session, invalid_data)
```

### Using Fixtures

```python
def test_with_fixtures(self, client, test_user, auth_headers):
    """Test using predefined fixtures."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert_response_success(response)
    
    data = response.json()
    assert data["id"] == test_user.id
```

### Mocking External Services

```python
def test_with_mocks(self, client, mock_firebase, mock_email_service):
    """Test with mocked external services."""
    # Firebase and email services are automatically mocked
    response = client.post("/api/v1/auth/register", json=user_data)
    assert_response_success(response, 201)
```

### Performance Testing

```python
@pytest.mark.performance
def test_performance(self, db_session):
    """Test performance requirements."""
    import time
    
    start_time = time.time()
    result = expensive_operation(db_session)
    end_time = time.time()
    
    # Assert performance requirements
    assert end_time - start_time < 1.0  # Should complete within 1 second
    assert result is not None
```

## Coverage Reports

### Generating Coverage Reports

```bash
# HTML report (recommended)
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Terminal report
pytest --cov=app --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Coverage Targets

- **Overall Coverage**: > 90%
- **Critical Components**: > 95%
- **New Code**: 100%

### Excluding Files from Coverage

Add to `.coveragerc`:

```ini
[run]
omit = 
    */tests/*
    */migrations/*
    */venv/*
    */env/*
```

## Continuous Integration

### GitHub Actions

The project uses GitHub Actions for automated testing:

- **On Push/PR**: Run unit, integration, and security tests
- **On Main Branch**: Additional performance tests
- **Daily**: Full security scan

### Pipeline Stages

1. **Lint**: Code formatting and style checks
2. **Unit Tests**: Fast, isolated tests
3. **Integration Tests**: API endpoint tests
4. **Security Tests**: Vulnerability scanning
5. **Performance Tests**: Load and stress testing (main branch only)

### Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/username/dreambig/workflows/Tests/badge.svg)
![Coverage](https://codecov.io/gh/username/dreambig/branch/main/graph/badge.svg)
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Ensure test database is accessible
export DATABASE_URL=sqlite:///./test.db

# Or use PostgreSQL for testing
export DATABASE_URL=postgresql://user:pass@localhost/test_db
```

#### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

#### Fixture Not Found

```python
# Ensure fixture is defined in conftest.py or imported
from app.tests.conftest import test_user, auth_headers
```

#### Slow Tests

```bash
# Run only fast tests
pytest -m "not slow"

# Use parallel execution
pytest -n auto

# Profile slow tests
pytest --durations=10
```

### Debugging Tests

```bash
# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables in traceback
pytest -l
```

### Test Data Cleanup

```python
# Use fixtures for automatic cleanup
@pytest.fixture
def test_data(db_session):
    # Create test data
    data = create_test_data(db_session)
    yield data
    # Cleanup happens automatically
```

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Independence**: Each test should be independent and not rely on others
3. **Test Data**: Use fixtures for consistent test data
4. **Assertions**: Use specific assertions with clear error messages
5. **Mocking**: Mock external dependencies to ensure test isolation
6. **Performance**: Keep tests fast; mark slow tests appropriately
7. **Coverage**: Aim for high coverage but focus on meaningful tests
8. **Documentation**: Document complex test scenarios and edge cases

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
