import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Force Matplotlib to use non-interactive backend 'Agg' for CI/Headless environments
import matplotlib
matplotlib.use('Agg')

# Monkeypatch platform module to prevent slow WMI calls on Windows
# CONSTANTLY checking WMI on every import causes massive hangs
import platform
import sys

if sys.platform == 'win32':
    platform.system = lambda: "Windows"
    platform.release = lambda: "10"
    platform.version = lambda: "10.0.19045"
    platform.machine = lambda: "AMD64"
    platform.processor = lambda: "Intel64 Family 6 Model 142 Stepping 9, GenuineIntel"
    platform.node = lambda: "DESKTOP-CI"
    platform.platform = lambda: "Windows-10-10.0.19045-SP0"
    platform.win32_ver = lambda: ("10", "10.0.19045", "SP0", "Multiprocessor Free")

MOCK_MODULES = [
    'chromadb',
    'chromadb.config', 
    'pysqlite3',
    'docling',
    'langchain_community.vectorstores',
    'embedchain',
    'newspaper',
    'newspaper.article',
    'duckduckgo_search',
    'lxml_html_clean',
    'spacy',
    'en_core_web_sm'
]

for mod_name in MOCK_MODULES:
    try:
        __import__(mod_name)
    except Exception: # Catch ImportError, RuntimeError, TypeError, etc.
        if mod_name not in sys.modules:
            mock_mod = MagicMock()
            # Shotgun Mocking: Set all common version attributes to prevent "MagicMock >= tuple" errors
            mock_mod.__version__ = "3.35.0"
            mock_mod.version_info = (3, 35, 0)
            mock_mod.VERSION = (3, 35, 0)
            mock_mod.sqlite_version_info = (3, 35, 0)
            mock_mod.sqlite_version = "3.35.0"
            
            # Handle pysqlite3.dbapi2.sqlite_version_info
            if mod_name == "pysqlite3":
                mock_mod.dbapi2 = MagicMock()
                mock_mod.dbapi2.sqlite_version_info = (3, 35, 0)
                mock_mod.dbapi2.sqlite_version = "3.35.0"
                mock_mod.dbapi2.version_info = (3, 35, 0)
                
            sys.modules[mod_name] = mock_mod

# Specific fix for ChromaDB checking sqlite3 version
# We must ensure sqlite3 has a compatible version string, even if it's the system one
import sqlite3
if sqlite3.sqlite_version_info < (3, 35, 0):
    # Monkey patch the version info if it's too old or missing
    # But checking 'sqlite_version_info' might be what's failing if it's a MagicMock?
    # No, if it's a MagicMock, we need to set it.
    pass

# Patch sqlite3 globally to ensure it passes checks
# Chroma does: if sqlite3.sqlite_version_info < (3, 35, 0): raise...
# We define a dummy sqlite3 shim if strictly needed, or just patch the existing one.
try:
    sqlite3.sqlite_version_info = (3, 35, 0)
    sqlite3.sqlite_version = "3.35.0"
except Exception:
    pass # Can't patch built-in types sometimes

# Mock CrewAI specifically if it's broken (e.g. checks for chromadb at runtime)
# We wrap this in a generally broad try/except to catch ANY initialization error
try:
    import crewai
    from crewai.tools import tool
except Exception: # Catch ImportError AND runtime errors (like missing sqlite binary)
    print("⚠️ CrewAI broken/missing. Mocking for test collection.")
    mock_crewai = MagicMock()
    mock_crewai.__version__ = "0.1.0"
    sys.modules["crewai"] = mock_crewai
    sys.modules["crewai.tools"] = MagicMock()
    sys.modules["crewai.process"] = MagicMock()
    sys.modules["crewai.agent"] = MagicMock()
    sys.modules["crewai.task"] = MagicMock()
    sys.modules["crewai.project"] = MagicMock()
    
    # Ensure 'tool' decorator works
    sys.modules["crewai.tools"].tool = lambda x: x

# Mock CrewAI specifically if it's broken (e.g. checks for chromadb at runtime)
# We wrap this in a generally broad try/except to catch ANY initialization error
try:
    import crewai
    from crewai.tools import tool
except Exception: # Catch ImportError AND runtime errors (like missing sqlite binary)
    print("⚠️ CrewAI broken/missing. Mocking for test collection.")
    mock_crewai = MagicMock()
    mock_crewai.__version__ = "0.1.0"
    sys.modules["crewai"] = mock_crewai
    sys.modules["crewai.tools"] = MagicMock()
    sys.modules["crewai.process"] = MagicMock()
    sys.modules["crewai.agent"] = MagicMock()
    sys.modules["crewai.task"] = MagicMock()
    sys.modules["crewai.project"] = MagicMock()
    
    # Ensure 'tool' decorator works
    sys.modules["crewai.tools"].tool = lambda x: x

# Add the project root directory to sys.path
# This ensures that 'rover_tools', 'utils', 'crew_engine', etc. can be imported by tests
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
