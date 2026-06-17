import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.bot.handlers import client, engineer, admin
    print("SUCCESS: All handlers imported successfully")
except Exception as e:
    print(f"ERROR: Failed to import handlers: {e}")
    sys.exit(1)