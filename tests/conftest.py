"""
conftest.py — Global pytest configuration for Market-Rover.

Strategy:
  1. Force matplotlib to use the non-interactive 'Agg' backend FIRST (before any import).
  2. Blind-mock heavy/unavailable packages so pytest collection never hangs.
  3. Guard crewai: try real import, fall back to a minimal mock if broken.
  4. Add project root to sys.path so all source modules are importable.

NOTE: Do NOT mock matplotlib.pyplot here — we rely on matplotlib.use('Agg') instead.
      Mocking plt as a MagicMock instance breaks seaborn/streamlit issubclass() checks.
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

# ── 3. Blind-mock heavy packages that cause hangs or are unavailable in CI ────
#    Do NOT add matplotlib.pyplot here — it breaks seaborn/streamlit.
BLIND_MOCK_MODULES = [
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
    'en_core_web_sm',
    'yfinance',
    'nselib',
    'nsepython',
    'langchain_google_genai',
    'google.generativeai',
    'google.ai.generativelanguage',
    # 'google' — DO NOT mock top-level google; it breaks protobuf
    'scikit-learn',
    'sklearn',
    'statsmodels',
    'prophet',
    'fbprophet',
    'pmdarima',
    'tensorflow',
    'torch',
    'keras',
    'cv2',
]

for _mod_name in BLIND_MOCK_MODULES:
    _mock = MagicMock()
    # Common version attributes expected by various libraries
    _mock.__version__ = "3.35.0"
    _mock.version_info = (3, 35, 0)
    _mock.VERSION = (3, 35, 0)
    _mock.sqlite_version_info = (3, 35, 0)
    _mock.sqlite_version = "3.35.0"

    # pysqlite3 needs a dbapi2 sub-module with version info
    if _mod_name == 'pysqlite3':
        _mock.dbapi2 = MagicMock()
        _mock.dbapi2.sqlite_version_info = (3, 35, 0)
        _mock.dbapi2.sqlite_version = "3.35.0"
        _mock.dbapi2.version_info = (3, 35, 0)

    # FIX: Classes used in issubclass() checks must be actual types, not instances.
    if _mod_name == 'langchain_google_genai':
        _mock.ChatGoogleGenerativeAI = MagicMock
        _mock.GoogleGenerativeAI = MagicMock

    if _mod_name == 'google.generativeai':
        _mock.GenerativeModel = MagicMock

    if _mod_name == 'prophet':
        _mock.Prophet = MagicMock

    if _mod_name == 'sklearn':
        _mock.base = MagicMock()
        _mock.base.BaseEstimator = MagicMock

    sys.modules[_mod_name] = _mock

# ── 4. sqlite3 version patch (ChromaDB checks sqlite3.sqlite_version_info) ────
import sqlite3
try:
    sqlite3.sqlite_version_info = (3, 35, 0)
    sqlite3.sqlite_version = "3.35.0"
except Exception:
    pass

# ── 5. CrewAI: try real import, fall back to minimal mock ────────────────────
try:
    import crewai  # noqa: F401
    from crewai.tools import tool  # noqa: F401
except Exception:
    _mock_crewai = MagicMock()
    _mock_crewai.__version__ = "0.1.0"
    # Key classes must be types (not instances) for issubclass() checks
    _mock_crewai.Agent = MagicMock
    _mock_crewai.Task = MagicMock
    _mock_crewai.Crew = MagicMock
    _mock_crewai.Process = MagicMock

    _mock_crewai_tools = MagicMock()
    _mock_crewai_tools.BaseTool = MagicMock  # type, not instance

    def _mock_tool(*args, **kwargs):
        """Robust @tool decorator mock — handles both @tool and @tool('name') usage."""
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]  # bare @tool usage
        return decorator

    _mock_crewai_tools.tool = _mock_tool

    sys.modules['crewai'] = _mock_crewai
    sys.modules['crewai.tools'] = _mock_crewai_tools
    sys.modules['crewai.process'] = MagicMock()
    sys.modules['crewai.agent'] = MagicMock()
    sys.modules['crewai.task'] = MagicMock()
    sys.modules['crewai.project'] = MagicMock()

# ── 6. Add project root to sys.path ──────────────────────────────────────────
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
