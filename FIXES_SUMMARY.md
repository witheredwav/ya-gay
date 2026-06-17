# Fixes Applied

## 1. Fixed incorrect import in `src/bot/keyboards/common.py`
- Changed `ReplyKeyboardKeyboardButton` to `KeyboardButton`

## 2. Fixed syntax error in `src/bot/keyboards/engineer.py`
- Changed `builder.button text=` to `builder.button(text=`

## 3. Added missing imports in handler files
- Added `from sqlalchemy import select` to:
  - `src/bot/handlers/client.py`
  - `src/bot/handlers/engineer.py`
  - `src/bot/handlers/admin.py`

## 4. Fixed model import in `src/models/user.py`
- Changed `from sqlalchemy.orm relationship` to `from sqlalchemy.orm import relationship`

## 5. Fixed `__init__.py` files to properly export modules
- `src/bot/handlers/__init__.py`: 
  - Added `from . import client, engineer, admin` and `__all__ = ["client", "engineer", "admin"]`
- `src/bot/keyboards/__init__.py`:
  - Added `from . import common, client, engineer, admin` and `__all__ = ["common", "client", "engineer", "admin"]`
- `src/bot/middlewares/__init__.py`:
  - Added `from .role_middleware import RoleMiddleware` and `__all__ = ["RoleMiddleware"]`

## 6. Updated database URL handling in `src/bot/database.py`
- Added function to ensure the database URL uses the `asyncpg` driver for SQLAlchemy's async engine.

## 7. Fixed migration issues
- Renamed migration file from `migrations/versions/20260618000000_initial_migration.py` to `migrations/versions/0001_initial.py`
- Updated revision ID in the migration file from `'20260618000000'` to `'0001_initial'`
- Fixed typo in downgrade function: `op.delete_table('referrals')` → `op.drop_table('referrals')`
- Completely rewrote `migrations/env.py` to:
  - Load environment variables from `.env` file using python-dotenv
  - Get `DATABASE_URL` directly from environment (with clear error if missing)
  - Convert asyncpg URL to synchronous PostgreSQL URL for Alembic migrations
  - Handle both offline and online migration modes correctly

## 8. Docker & Deployment Improvements
- Updated `Dockerfile` to run migrations before starting the bot:
  ```dockerfile
  CMD ["sh", "-c", "python -m alembic upgrade head && python -m src.bot.main"]
  ```
- Enhanced `docker-compose.yml` with:
  - Database healthcheck (waits for PostgreSQL to be ready)
  - Service dependency with `condition: service_healthy` (bot waits for healthy DB)
  - Volume persistence for database data

## 9. Requirements Update
- Added `psycopg2-binary==2.9.9` to `requirements.txt` for Alembic's synchronous operations

## Troubleshooting
### Multiple head revisions error
If you see an error like:
```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
```
This means your database has an old migration stamp from a previous run. To fix this:

#### For Docker Compose:
```bash
docker-compose down -v   # This removes the database volume and starts fresh
docker-compose up --build
```

#### For Railway:
You may need to reset/delete your PostgreSQL plugin and re-add it to start with a clean database.

#### For local development (without Docker):
Drop your database and recreate it, then run:
```bash
alembic upgrade head
```

## Next Steps
1. Set up a PostgreSQL database (either locally or using Docker Compose)
2. Copy `.env.example` to `.env` and fill in the correct values
3. Run database migrations: `alembic upgrade head` (or let Docker Compose/Railway handle it)
4. Start the bot: `python -m src.bot.main` (or via Docker Compose/Railway)

The bot should now start without import or migration errors.