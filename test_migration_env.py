import os
import sys

# Set a dummy DATABASE_URL for testing
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/db"

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    # Try to import the migration environment
    from migrations.env import get_sync_url
    url = get_sync_url()
    print(f"SUCCESS: get_sync_url returned: {url}")
    # Check that it's converted to synchronous
    assert url.startswith("postgresql://")
    print("SUCCESS: URL is correctly converted to synchronous format")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)