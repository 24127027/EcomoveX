# EcomoveX Backend Testing Guide

## Overview
This directory contains comprehensive test suites for all backend endpoints of the EcomoveX API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Test fixtures and configuration
├── test_root.py             # Root endpoint tests
├── test_authentication.py   # Authentication tests (register, login)
├── test_user.py            # User management tests
├── test_carbon.py          # Carbon emission tracking tests
├── test_review.py          # Review management tests
└── test_reward.py          # Rewards and missions tests
```

## Test Coverage

### 1. Authentication (`test_authentication.py`)
- User registration (success, duplicate email/username)
- User login (success, invalid credentials)
- Email validation

### 2. User Management (`test_user.py`)
- Get user profile (authenticated/unauthenticated)
- Get user by ID
- Update user credentials
- Update user profile
- Delete user account
- Add eco points (admin only)

### 3. Carbon Emissions (`test_carbon.py`)
- Calculate and create carbon emissions
- Get user's carbon emissions
- Get total carbon footprint
- Get carbon by day/week/month/year/range
- Update/delete carbon emissions
- Invalid data validation

### 4. Reviews (`test_review.py`)
- Create reviews
- Get reviews by destination/user
- Get user's own reviews
- Update/delete reviews
- Rating validation

### 5. Rewards & Missions (`test_reward.py`)
- Get all missions
- Create missions (admin only)
- Get mission by ID/name
- Update missions (admin only)
- Complete missions
- Get completed missions

## Setup

1. **Install test dependencies:**
   ```bash
   pip install pytest pytest-asyncio httpx
   ```

2. **Ensure PostgreSQL is running:**
   - The tests will create test databases automatically
   - Test databases: `test_ecomoveX_users` and `test_ecomoveX_destinations`

3. **Configure environment:**
   - Make sure `.env` file is properly configured
   - Test databases will be separate from production databases

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with verbose output:
```bash
pytest -v
```

### Run specific test file:
```bash
pytest tests/test_authentication.py
```

### Run specific test:
```bash
pytest tests/test_user.py::TestUserEndpoints::test_get_my_profile
```

### Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

### Use PowerShell script:
```powershell
.\run_tests.ps1
```

## Test Fixtures

### Database Fixtures
- `setup_test_databases`: Creates/drops test databases
- `db_session`: Provides test database session
- `dest_db_session`: Provides test destination database session

### Authentication Fixtures
- `test_user_token`: Creates test user and returns JWT token
- `test_admin_token`: Creates admin user and returns JWT token
- `auth_headers`: Returns authorization headers for regular user
- `admin_auth_headers`: Returns authorization headers for admin

### Client Fixture
- `client`: Async HTTP client with database overrides

## Writing New Tests

Example test structure:

```python
import pytest
from httpx import AsyncClient

class TestMyFeature:
    """Test my feature endpoints"""
    
    @pytest.mark.asyncio
    async def test_something(self, client: AsyncClient, test_user_token: str):
        """Test description"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = await client.get("/my-endpoint", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

## Common Assertions

```python
# Status codes
assert response.status_code == 200  # Success
assert response.status_code == 201  # Created
assert response.status_code == 400  # Bad Request
assert response.status_code == 401  # Unauthorized
assert response.status_code == 403  # Forbidden
assert response.status_code == 404  # Not Found
assert response.status_code == 422  # Validation Error

# Response data
data = response.json()
assert "field_name" in data
assert data["field"] == expected_value
assert isinstance(data, list)
assert len(data) > 0
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify test database permissions

### Test Failures
- Check test database state (tests should be independent)
- Verify environment variables
- Check for port conflicts

### Async Issues
- Ensure all test functions are marked with `@pytest.mark.asyncio`
- Use `await` for async operations
- Check event loop configuration

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    cd backend
    pytest -v --tb=short
```

## Notes

- Tests use separate test databases to avoid affecting production data
- Each test function runs with a fresh database state
- Authentication tokens are generated automatically for authenticated tests
- Admin tests require admin role fixtures
