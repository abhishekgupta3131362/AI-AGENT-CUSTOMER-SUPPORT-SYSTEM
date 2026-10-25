import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app import create_app
from backend.config import Config

if __name__ == "__main__":
    app = create_app()
    print("=" * 65)
    print("  APEXTECH AI AGENT-BASED CUSTOMER SUPPORT SYSTEM")
    print("=" * 65)
    print(f"  * Local Web App: http://127.0.0.1:{Config.PORT}")
    print(f"  * REST API Base: http://127.0.0.1:{Config.PORT}/api")
    print(f"  * Active LLM   : {Config.DEFAULT_LLM_PROVIDER.upper()}")
    print("=" * 65)
    app.run(host="127.0.0.1", port=Config.PORT, debug=Config.DEBUG)
