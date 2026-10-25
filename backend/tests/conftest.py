"""Global pytest fixtures and sys.path resolution for VendorShield backend tests.

Ensures that imports like 'from backend.app...' and 'from app...' resolve consistently
regardless of test runner working directory.
"""
import sys
import os
from pathlib import Path

# Add backend directory and repository root to sys.path
backend_dir = Path(__file__).resolve().parent.parent
repo_root = backend_dir.parent

for p in (str(backend_dir), str(repo_root)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Unless explicitly running live integration tests, ensure deterministic simulated fixtures
if "TEST_LIVE_TINYFISH" not in os.environ:
    os.environ["TINYFISH_API_KEY"] = ""
    try:
        from app.config import settings
        settings.TINYFISH_API_KEY = ""
    except Exception:
        pass

