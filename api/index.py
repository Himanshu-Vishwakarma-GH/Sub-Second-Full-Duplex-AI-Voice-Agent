import sys
from pathlib import Path

# Add backend directory to sys.path so server.py and its dependencies resolve
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from server import app

