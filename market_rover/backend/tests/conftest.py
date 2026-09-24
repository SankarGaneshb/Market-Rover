"""
conftest.py — Test bootstrap for market_rover/backend/tests/

Problem: agent nodes import from rover_tools.* which is a root-level
         Streamlit package, not available inside market_rover/backend/.

Solution: Inject stub MagicMock modules for every rover_tools sub-package
          before any test module is collected. This means all rover_tools
          imports resolve to MagicMock objects — which is exactly what the
          test suite patches over anyway.
"""
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so real rover_tools is accessible
_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))
