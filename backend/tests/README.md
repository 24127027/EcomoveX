# EcomoveX Backend Tests

## Overview
Comprehensive test suite for all repositories and services in the EcomoveX backend.

## Test Structure

```
tests/
├── conftest.py                      # Test configuration and fixtures
├── test_user_repository.py          # User CRUD operations
├── test_destination_repository.py   # Destination CRUD operations
├── test_carbon_repository.py        # Carbon emission tracking
├── test_plan_repository.py          # Travel plans and destinations
└── test_review_repository.py        # Reviews (cross-database)
```

## What is Tested

### Repositories
- ✅ **UserRepository**: Create, read, update, delete users
- ✅ **DestinationRepository**: Destination management in separate DB
- ✅ **CarbonRepository**: Carbon emission tracking and calculations
- ✅ **PlanRepository**: Plan creation and destination management
- ✅ **ReviewRepository**: Reviews with cross-database validation

### Key Features Tested
1. **Database Separation**: Tests verify both databases work independently
2. **Cross-Database Operations**: Plan destinations and reviews reference destination DB
3. **CRUD Operations**: Full create, read, update, delete for all models
4. **Data Integrity**: Foreign keys, cascades, and relationships
5. **Business Logic**: Carbon totals, user profiles, plan destinations

## Running Tests

### Prerequisites
1. PostgreSQL server running on localhost:5432
2. Python virtual environment activated
3. Required packages installed:
   ```bash
   pip install pytest pytest-asyncio asyncpg sqlalchemy
   ```

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test File
```bash
pytest tests/test_user_repository.py -v
```

### Run Specific Test
```bash
pytest tests/test_user_repository.py::test_create_user -v
```

## Test Databases

Tests use separate databases from production:
- **User Test DB**: `test_ecomovex_users`
- **Destination Test DB**: `test_ecomovex_destinations`

These are automatically created by `run_tests.py` and cleaned up after tests.

## Test Coverage

### User Repository (6 tests)
- Create user with default values
- Get user by email
- Get user by ID
- Update user credentials (username, email)
- Update user profile (eco_point, rank)
- Delete user

### Destination Repository (5 tests)
- Create destination
- Get destination by ID
- Get destination by coordinates
- Update destination
- Delete destination

### Carbon Repository (4 tests)
- Create carbon emission record
- Get all emissions by user
- Calculate total carbon by user
- Delete carbon emission

### Plan Repository (6 tests)
- Create plan
- Get plans by user
- Add destination to plan (cross-database)
- Get plan destinations
- Update plan
- Delete plan

### Review Repository (5 tests)
- Create review (cross-database)
- Get reviews by destination
- Get reviews by user
- Update review
- Delete review

## Expected Output

```
==================================================================
  EcomoveX Backend Tests
==================================================================

🔧 Setting up test databases...
✅ Created test user database
✅ Created test destination database

🧪 Running tests...

tests/test_carbon_repository.py::test_create_carbon_emission PASSED
tests/test_carbon_repository.py::test_get_carbon_emissions_by_user PASSED
tests/test_carbon_repository.py::test_get_total_carbon_by_user PASSED
tests/test_carbon_repository.py::test_delete_carbon_emission PASSED
tests/test_destination_repository.py::test_create_destination PASSED
tests/test_destination_repository.py::test_get_destination_by_id PASSED
tests/test_destination_repository.py::test_get_destination_by_coordinates PASSED
tests/test_destination_repository.py::test_update_destination PASSED
tests/test_destination_repository.py::test_delete_destination PASSED
tests/test_plan_repository.py::test_create_plan PASSED
tests/test_plan_repository.py::test_get_plan_by_user PASSED
tests/test_plan_repository.py::test_add_destination_to_plan PASSED
tests/test_plan_repository.py::test_get_plan_destinations PASSED
tests/test_plan_repository.py::test_update_plan PASSED
tests/test_plan_repository.py::test_delete_plan PASSED
tests/test_review_repository.py::test_create_review PASSED
tests/test_review_repository.py::test_get_reviews_by_destination PASSED
tests/test_review_repository.py::test_get_reviews_by_user PASSED
tests/test_review_repository.py::test_update_review PASSED
tests/test_review_repository.py::test_delete_review PASSED
tests/test_user_repository.py::test_create_user PASSED
tests/test_user_repository.py::test_get_user_by_email PASSED
tests/test_user_repository.py::test_get_user_by_id PASSED
tests/test_user_repository.py::test_update_user_credentials PASSED
tests/test_user_repository.py::test_update_user_profile PASSED
tests/test_user_repository.py::test_delete_user PASSED

==================================================================
  ✅ ALL TESTS PASSED! (26 passed)
==================================================================
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check credentials in `conftest.py` match your setup
- Verify postgres user has CREATE DATABASE privileges

### Import Errors
- Ensure virtual environment is activated
- Install all dependencies: `pip install -r requirements.txt`
- Check Python path includes backend directory

### Test Failures
- Check database state (may need manual cleanup)
- Review test output for specific error messages
- Ensure both test databases are accessible

## Notes

- Tests are isolated and use transactions that rollback after each test
- Each test creates fresh data to avoid dependencies
- Cross-database tests verify both user and destination databases work together
- Tests run in parallel-safe mode (each test is independent)
