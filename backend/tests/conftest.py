"""Global pytest fixtures and sys.path resolution for VendorShield backend tests.

Ensures that imports like 'from backend.app...' and 'from app...' resolve consistently
regardless of test runner working directory.
"""
import sys
from pathlib import Path

# Add backend directory and repository root to sys.path
backend_dir = Path(__file__).resolve().parent.parent
repo_root = backend_dir.parent

for p in (str(backend_dir), str(repo_root)):
    if p not in sys.path:
        sys.path.insert(0, p)
