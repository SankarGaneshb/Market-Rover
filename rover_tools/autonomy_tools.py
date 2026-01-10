"""
Autonomy Tools - Agent Tools for Decision Logging
"""
from utils.autonomy_logger import log_autonomy_event
try:
    from crewai.tools import tool
except ImportError:
    def tool(name_or_func):
        def decorator(func):
            return func
        return decorator

@tool("Announce Market Regime")
def announce_regime_tool(regime: str, reason: str) -> str:
    """
    Announce the detected Market Regime (DEFENSIVE or GROWTH).
    Use this immediately after checking Global Cues (VIX/Crude).
    
    Args:
        regime: "DEFENSIVE" or "GROWTH"
        reason: Why? (e.g. "VIX is 24", "Crude is stable")
    """
    regime = regime.upper()
    log_autonomy_event(role="Strategist", event_type=f"REGIME_CHANGE: {regime}", details=reason)
    return f"REGIME SET TO {regime}. Downstream agents notified."

@tool("Log Tool Pivot")
def log_pivot_tool(missing_tool: str, pivot_tool: str, reason: str) -> str:
    """
    Log when you pivot to a backup tool because primary data was missing.
    
    Args:
        missing_tool: The tool that failed/returned empty (e.g. "Block Deals").
        pivot_tool: The tool you are switching to (e.g. "Sector Flow").
        reason: Explanation.
    """
    log_autonomy_event(role="Shadow/Strategist", event_type="TOOL_PIVOT", 
                       details=f"Missing {missing_tool} -> Switched to {pivot_tool}. Reason: {reason}")
    return "Pivot logged successfully."
