import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
from migrations.env import get_sync_url
print(get_sync_url())