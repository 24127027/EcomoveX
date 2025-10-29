# Real User & Authentication Service Implementation

## Overview
This document describes the implementation of secure user management and authentication services for EcomoveX backend.

## Architecture

```
main.py
├── authentication_router (POST /auth/register, /auth/login)
└── user_router (GET/PUT/DELETE /users/*)
    ├── UserService (Business Logic Layer)
    │   ├── Password hashing with bcrypt
    │   ├── User CRUD operations
    │   └── Eco points & ranking system
    └── AuthenticationService (Authentication Layer)
        ├── JWT token generation
        ├── Password verification
        └── User login/registration
```

## Key Features Implemented

### 1. **Authentication Service** (`services/authentication_service.py`)
- ✅ JWT token generation with user ID and role
- ✅ Bcrypt password hashing (rounds=12)
- ✅ Secure login with password verification
- ✅ User registration with duplicate email check
- ✅ Error handling and proper HTTP status codes

### 2. **User Service** (`services/user_service.py`)
- ✅ User CRUD operations
- ✅ Password hashing for new users
- ✅ Secure credential updates with old password verification
- ✅ Eco points management with auto-ranking
- ✅ Comprehensive error handling

### 3. **Security Features**
- ✅ **Password Hashing**: Bcrypt with automatic salt generation
- ✅ **JWT Tokens**: Signed with SECRET_KEY from environment
- ✅ **Password Verification**: Constant-time comparison via bcrypt
- ✅ **Authorization**: JWT middleware for protected routes

## API Endpoints

### Authentication Endpoints (`/auth`)

#### POST /auth/register
Register a new user with hashed password.

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "user_id": 1,
  "role": "user",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "user_id": 1,
  "role": "user",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### User Endpoints (`/users`)

#### GET /users/me
Get authenticated user's profile (requires JWT).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "eco_point": 150,
  "rank": "bronze",
  "role": "user",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### PUT /users/me
Update user profile (requires JWT).

**Request:**
```json
{
  "eco_point": 600,
  "rank": "silver"
}
```

#### PUT /users/me/credentials
Update email/password (requires JWT + old password).

**Request:**
```json
{
  "old_password": "SecurePass123!",
  "new_email": "newemail@example.com",
  "new_password": "NewSecurePass456!"
}
```

#### DELETE /users/me
Delete user account (requires JWT).

## Security Implementation Details

### Password Hashing
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password on registration
hashed = pwd_context.hash(plain_password)

# Verify password on login
is_valid = pwd_context.verify(plain_password, hashed_password)
```

### JWT Token Structure
```json
{
  "sub": "1",        // User ID as string
  "role": "user"     // User role (user/admin)
}
```

### Environment Configuration
Required in `local.env`:
```env
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
DB_USER=postgres
DB_PASS=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecomovex
```

## Ranking System

The eco points automatically determine user rank:

| Points Range | Rank |
|-------------|------|
| 0 - 500 | Bronze |
| 501 - 2000 | Silver |
| 2001 - 5000 | Gold |
| 5001 - 10000 | Platinum |
| 10001+ | Diamond |

## Error Handling

All services implement comprehensive error handling:

- **400 Bad Request**: Invalid input, duplicate email
- **401 Unauthorized**: Invalid credentials, wrong password
- **404 Not Found**: User not found
- **500 Internal Server Error**: Database or unexpected errors

## Testing

All endpoints are tested with 14 comprehensive test cases:
- ✅ User registration (success, duplicate, validation)
- ✅ User login (success, wrong password)
- ✅ Profile management (get, update)
- ✅ Credential updates (email, password)
- ✅ Account deletion

Run tests:
```bash
pytest backend/tests/test_user_api.py -v
```

## Files Modified/Created

1. **services/authentication_service.py** - Authentication logic
2. **services/user_service.py** - User business logic
3. **routers/authentication_router.py** - Auth API endpoints
4. **routers/user_router.py** - User API endpoints
5. **main.py** - FastAPI application with routers
6. **utils/authentication_util.py** - JWT verification middleware

## Dependencies

Required Python packages (in requirements.txt):
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

## Usage Example

```python
# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Register a new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"pass123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"pass123"}'

# Get profile (with token)
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer <your_token_here>"
```

## Next Steps

1. ✅ Services implemented and integrated
2. ✅ Security features (bcrypt, JWT) in place
3. ✅ All routes connected to main.py
4. ⏳ Fix remaining bugs for 100% test pass rate
5. 🔄 Add rate limiting for auth endpoints
6. 🔄 Implement refresh tokens
7. 🔄 Add email verification
8. 🔄 Add password reset functionality
