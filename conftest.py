# Root-level conftest.py
# ─────────────────────────────────────────────────────────────────────────────
# Ensures the project root (the directory containing `app/`) is on sys.path
# so that `import app.xxx` works when running pytest from any working directory.
#
# This complements the `pythonpath = ["."]` setting in pyproject.toml and
# acts as a fallback for pytest versions < 7.0 that don't support that key.
# ─────────────────────────────────────────────────────────────────────────────

import sys
from pathlib import Path

# Insert project root at the front of sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))