# Fixing the Missing is_admin Column Error

## Problem
The bot is crashing with the error:
```
ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) 
<class 'asyncpg.exceptions.UndefinedColumnError'>: column users.is_admin does not exist
```

This occurs because migration `0002_add_is_admin_column.py` has not been applied to the database. This migration adds the `is_admin` column to the `users` table.

## Solution

### Option 1: Apply the Migration (Recommended)
If you can connect to your database, run:
```bash
py -m alembic upgrade head
```

### Option 2: Manual SQL Execution
If you cannot run Alembic due to connection issues, execute this SQL directly on your PostgreSQL database:
```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
```

### Option 3: Reset Database (Development Only)
If you're in a development environment and don't mind losing data:
1. Drop your database and recreate it
2. Run: `py -m alembic upgrade head` to apply all migrations

## Verification
After applying the fix, verify the column exists:
```sql
\d users
```
You should see `is_admin` column in the table schema.

## Notes
- The migration sets a server default of `FALSE` for existing rows
- New users will automatically have `is_admin = false` unless explicitly set
- This column is used by the RoleMiddleware to determine admin access