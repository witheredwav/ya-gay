import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set dummy environment variables for testing
os.environ.setdefault("BOT_TOKEN", "dummy_token")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/db_name")
os.environ.setdefault("ADMIN_IDS", "123456789,987654321")

try:
    from src.bot.handlers import client, engineer, admin
    print("SUCCESS: All handlers imported successfully")
except Exception as e:
    print(f"ERROR: Failed to import handlers: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)