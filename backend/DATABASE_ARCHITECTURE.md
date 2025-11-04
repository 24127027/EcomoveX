# Database Architecture - Two Separate Databases

## Overview
The EcomoveX backend uses **two separate PostgreSQL databases** for better fault isolation and scalability:

1. **User Database** (`ecomoveX_users`) - Main application database
2. **Destination Database** (`ecomoveX_destinations`) - Isolated destination data

## Database Configuration

### User Database
- **Database Name**: `ecomoveX_users` (from `settings.USER_DB_NAME`)
- **Engine**: `user_engine` in `database/user_database.py`
- **Session**: `UserAsyncSessionLocal`
- **Base**: `UserBase`
- **Dependency**: `get_db()` - Use in routers/services for user-related data

### Destination Database  
- **Database Name**: `ecomoveX_destinations` (from `settings.DEST_DB_NAME`)
- **Engine**: `destination_engine` in `database/destination_database.py`
- **Session**: `DestinationAsyncSessionLocal`
- **Base**: `DestinationBase`
- **Dependency**: `get_destination_db()` - Use in routers/services for destination data

## Tables by Database

### User Database Tables (use `get_db()`)
- `users` - User accounts and profiles
- `carbon_emissions` - Carbon tracking records
- `reviews` - User reviews (stores destination_id as Integer, no FK)
- `media_files` - Uploaded files
- `messages` - Chatbot messages
- `missions` - Available missions/rewards
- `mission_users` - User mission completions
- `plans` - Travel plans
- `plan_destinations` - Plan destinations (stores destination_id as Integer, no FK)

### Destination Database Tables (use `get_destination_db()`)
- `destinations` - Destination locations (id, name, longitude, latitude)

## Important Notes on Foreign Keys

### ❌ Cross-Database Foreign Keys Removed
Since PostgreSQL doesn't support foreign keys across databases, we've removed FK constraints:

1. **reviews.destination_id** - No longer has FK to destinations.id
2. **plan_destinations.destination_id** - No longer has FK to destinations.id

These fields are now plain `Integer` columns. Application logic must ensure referential integrity.

### ✅ Within-Database Foreign Keys (Still Work)
- `reviews.user_id` → `users.id` (both in user DB)
- `carbon_emissions.user_id` → `users.id` (both in user DB)
- `plan_destinations.plan_id` → `plans.id` (both in user DB)
- etc.

## Repository Guidelines

### User Database Repositories (use standard `db: AsyncSession`)
All repositories EXCEPT `DestinationRepository`:
- `carbon_repository.py`
- `media_repository.py`
- `message_repository.py`
- `mission_repository.py`
- `plan_repository.py`
- `review_repository.py`
- `user_repository.py`

These all work with `get_db()` session from the user database.

### Destination Database Repository (use `db: AsyncSession` from destination DB)
- `destination_repository.py`

This repository expects an `AsyncSession` from `get_destination_db()`.

## Usage in Routers

### For User-Related Data
```python
from database.user_database import get_db

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await UserService.get_user_by_id(db, user_id)
```

### For Destination Data
```python
from database.destination_database import get_destination_db

@router.get("/destinations/{dest_id}")
async def get_destination(
    dest_id: int, 
    db: AsyncSession = Depends(get_destination_db)
):
    return await DestinationService.get_destination_by_id(db, dest_id)
```

### For Mixed Access (Both Databases)
If a service needs both databases:
```python
from database.user_database import get_db
from database.destination_database import get_destination_db

@router.get("/reviews/{review_id}")
async def get_review_with_destination(
    review_id: int,
    user_db: AsyncSession = Depends(get_db),
    dest_db: AsyncSession = Depends(get_destination_db)
):
    review = await ReviewService.get_review_by_id(user_db, review_id)
    destination = await DestinationService.get_destination_by_id(
        dest_db, 
        review.destination_id
    )
    return {"review": review, "destination": destination}
```

## Benefits of Separation

1. **Fault Isolation**: If destination DB goes down, users can still login/use other features
2. **Performance**: Separate connection pools reduce contention
3. **Scalability**: Can scale databases independently based on usage
4. **Maintenance**: Can backup/restore/migrate databases separately

## Initialization Scripts

- `init_all_databases.py` - Create both databases and all tables
- `reset_all_databases.py` - Drop and recreate both databases
- `drop_all_databases.py` - Drop both databases
- `models/init_user_database.py` - Initialize user DB tables only
- `models/init_destination_database.py` - Initialize destination DB tables only
