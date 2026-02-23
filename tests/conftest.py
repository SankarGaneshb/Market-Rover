"""
conftest.py — Global pytest configuration for Market-Rover.

Strategy:
  1. Force matplotlib to use the non-interactive 'Agg' backend FIRST.
  2. Only mock packages that are GENUINELY unavailable (not in requirements.txt).
     DO NOT mock packages that install successfully — replacing real modules with
     MagicMock() instances causes issubclass() failures when pydantic/other code
     checks isinstance/issubclass against those mocked classes.
  3. Add project root to sys.path.
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# ── 1. Matplotlib backend (must happen before any matplotlib import) ──────────
import matplotlib
matplotlib.use('Agg')

# ── 2. Platform monkeypatch (prevents slow WMI calls on Windows CI) ───────────
import platform
if sys.platform == 'win32':
    platform.system = lambda: "Windows"
    platform.release = lambda: "10"
    platform.version = lambda: "10.0.19045"
    platform.machine = lambda: "AMD64"
    platform.processor = lambda: "Intel64 Family 6 Model 142 Stepping 9, GenuineIntel"
    platform.node = lambda: "DESKTOP-CI"
    platform.platform = lambda: "Windows-10-10.0.19045-SP0"
    platform.win32_ver = lambda: ("10", "10.0.19045", "SP0", "Multiprocessor Free")

# ── 3. Add project root to sys.path ──────────────────────────────────────────
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
