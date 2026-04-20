"""
conftest.py — Test bootstrap for market_rover/backend/tests/

Problem: agent nodes import from rover_tools.* which is a root-level
         Streamlit package, not available inside market_rover/backend/.

Solution: Inject stub MagicMock modules for every rover_tools sub-package
          before any test module is collected. This means all rover_tools
          imports resolve to MagicMock objects — which is exactly what the
          test suite patches over anyway.
"""
import sys
import types
from unittest.mock import MagicMock


def _stub_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__spec__ = None  # prevents importlib from trying to reload it
    return mod


# ── Stub every rover_tools sub-package needed by agent nodes ──────────────────

_RT_SUBS = [
    "rover_tools",
    "rover_tools.advanced_skills",
    "rover_tools.global_market_tool",
    "rover_tools.shadow_tools",
    "rover_tools.portfolio_tool",
    "rover_tools.ticker_resources",
    "rover_tools.analytics",
    "rover_tools.analytics.forensic_engine",
]

for _mod_name in _RT_SUBS:
    if _mod_name not in sys.modules:
        _mod = _stub_module(_mod_name)
        sys.modules[_mod_name] = _mod

# Attach MagicMock callables for every symbol the agent nodes import
_adv = sys.modules["rover_tools.advanced_skills"]
_adv.analyze_retail_sentiment_tool   = MagicMock(return_value="Neutral market breadth.")
_adv.calculate_mtc_score_tool        = MagicMock(return_value="MTC Score: 55/100")
_adv.detect_technical_patterns_tool  = MagicMock(return_value="No patterns detected.")
_adv.fetch_subha_muhurtham_tool      = MagicMock(return_value="Check almanac.")

_glob = sys.modules["rover_tools.global_market_tool"]
_glob.get_global_cues_data           = MagicMock(return_value={"vix": 15, "dxy": 101, "yield_10y": 3.5})
_glob.get_global_cues                = _glob.get_global_cues_data

_shadow = sys.modules["rover_tools.shadow_tools"]
_shadow.get_trap_indicator_tool      = MagicMock(return_value="No institutional trap detected.")
_shadow.analyze_sector_flow_tool     = MagicMock(return_value="Sector flow neutral.")

_port = sys.modules["rover_tools.portfolio_tool"]
_port.read_portfolio                 = MagicMock(return_value=[])

_ticker = sys.modules["rover_tools.ticker_resources"]
_ticker.NIFTY_50_SECTOR_MAP          = {}

_forensic_pkg = sys.modules["rover_tools.analytics.forensic_engine"]
_forensic_pkg.ForensicAnalyzer       = MagicMock()
