import sys
import os
from pathlib import Path

# Add project root directory to sys.path so 'backend' can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
