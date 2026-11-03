"""
rover_tools/tool_guard.py

Centralized System Guardrails for Agent Tool Execution:
1. Tool Error Shielding: Catches unhandled tool exceptions and converts them
   into deterministic, advisory strings so agents do not enter runaway retry loops.
2. Output Length Pruning: Caps oversized tool payloads (e.g., massive HTML/scrapes)
   to a governed character ceiling to preserve prompt context and token budget.
"""

import functools
import logging
from typing import Any, Callable

logger = logging.getLogger("rover_tools.tool_guard")

# Default character ceiling (~800-900 tokens)
DEFAULT_MAX_TOOL_CHARS = 3500


def prune_and_shield_callable(
    func: Callable,
    tool_name: str = "",
    max_chars: int = DEFAULT_MAX_TOOL_CHARS,
    fallback_guidance: str = "Proceed with baseline historical data or heuristic assumptions."
) -> Callable:
    """
    Wraps an execution function with exception shielding and output length pruning.
    """
    t_name = tool_name or getattr(func, "__name__", "unknown_tool")

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            raw_result = func(*args, **kwargs)
            str_result = str(raw_result)
            if len(str_result) > max_chars:
                pruned = str_result[:max_chars]
                omitted = len(str_result) - max_chars
                return (
                    f"{pruned}\n\n"
                    f"[NOTICE: Tool output pruned. {omitted} characters omitted to stay within token budget.]"
                )
            return raw_result
        except Exception as e:
            err_type = type(e).__name__
            logger.warning(
                f"⚠️ Tool '{t_name}' execution shielded from crash: {err_type}: {e}"
            )
            return (
                f"[ADVISORY] Tool '{t_name}' temporarily unavailable ({err_type}). "
                f"Do not retry this tool immediately. {fallback_guidance}"
            )

    return wrapper


def shield_crewai_tool(tool_obj: Any, max_chars: int = DEFAULT_MAX_TOOL_CHARS) -> Any:
    """
    Applies pruning and error-shielding to a CrewAI Tool / BaseTool or callable.
    """
    if tool_obj is None:
        return None

    # Handle LangChain / CrewAI BaseTool or StructuredTool
    if hasattr(tool_obj, "_run") and callable(getattr(tool_obj, "_run")):
        orig_run = tool_obj._run
        tool_name = getattr(tool_obj, "name", "tool")
        tool_obj._run = prune_and_shield_callable(
            orig_run, tool_name=tool_name, max_chars=max_chars
        )
        return tool_obj

    # Handle callable tools
    if callable(tool_obj):
        return prune_and_shield_callable(tool_obj, max_chars=max_chars)

    return tool_obj
