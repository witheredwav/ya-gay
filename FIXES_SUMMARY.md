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

# Next Steps
1. Set up a PostgreSQL database (either locally or using Docker Compose)
2. Copy `.env.example` to `.env` and fill in the correct values
3. Run database migrations: `alembic upgrade head`
4. Start the bot: `python -m src.bot.main` (or via Docker Compose)

The bot should now start without import errors.