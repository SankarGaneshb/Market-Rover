"""
rover_tools/tool_guard.py

Centralized System Guardrails for Agent Tool Execution:
1. Tool Error Shielding: Catches unhandled tool exceptions and converts them
   into deterministic, advisory strings so agents do not enter runaway retry loops.
2. Output Length Pruning: Caps oversized tool payloads (e.g., massive HTML/scrapes)
   to a governed character ceiling to preserve prompt context and token budget.
3. Stateful Tool Circuit Breaker: Tracks consecutive tool failures and trips
   fast-fail status after a threshold to prevent hammering failing third-party APIs.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("rover_tools.tool_guard")

# Default character ceiling (~800-900 tokens)
DEFAULT_MAX_TOOL_CHARS = 3500
DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_RESET_TIMEOUT_SEC = 300.0  # 5 minutes


class ToolCircuitBreaker:
    """
    In-memory stateful circuit breaker for agent tools.
    Prevents repeated invocations of third-party endpoints or APIs that are
    experiencing continuous outages or rate-limit blocks.
    """

    def __init__(
        self,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        reset_timeout_sec: float = DEFAULT_RESET_TIMEOUT_SEC,
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout_sec = reset_timeout_sec
        self._failures: Dict[str, int] = {}
        self._last_state_change: Dict[str, float] = {}

    def record_success(self, tool_name: str) -> None:
        """Reset consecutive failures on a successful execution."""
        self._failures[tool_name] = 0

    def record_failure(self, tool_name: str) -> bool:
        """Record a failure; returns True if the breaker tripped."""
        count = self._failures.get(tool_name, 0) + 1
        self._failures[tool_name] = count
        if count >= self.failure_threshold:
            self._last_state_change[tool_name] = time.time()
            logger.warning(
                f"[CIRCUIT_BREAKER_TRIPPED] Tool '{tool_name}' failed {count} consecutive times. "
                f"Tripping circuit breaker for {self.reset_timeout_sec}s to avoid wasted quota."
            )
            return True
        return False

    def is_tripped(self, tool_name: str) -> bool:
        """Check if circuit breaker is open (tripped) for the specified tool."""
        if self._failures.get(tool_name, 0) < self.failure_threshold:
            return False
        # Check if reset timeout elapsed
        last_tripped = self._last_state_change.get(tool_name, 0.0)
        if (time.time() - last_tripped) > self.reset_timeout_sec:
            logger.info(
                f"[CIRCUIT_BREAKER_HALF_OPEN] Cooldown period elapsed for tool '{tool_name}'. Permitting retry."
            )
            self._failures[tool_name] = 0
            return False
        return True

    def reset_all(self) -> None:
        """Clear all failure counters."""
        self._failures.clear()
        self._last_state_change.clear()


# Global singleton circuit breaker instance
global_circuit_breaker = ToolCircuitBreaker()


def prune_and_shield_callable(
    func: Optional[Callable] = None,
    *,
    tool_name: str = "",
    max_chars: int = DEFAULT_MAX_TOOL_CHARS,
    fallback_guidance: str = "Proceed with baseline historical data or heuristic assumptions.",
    circuit_breaker: ToolCircuitBreaker = global_circuit_breaker,
) -> Callable:
    """
    Wraps an execution function with circuit-breaker checks, exception shielding, and output length pruning.
    Can be used as @prune_and_shield_callable or @prune_and_shield_callable(...) or invoked directly.
    """

    def decorator(fn: Callable) -> Callable:
        t_name = tool_name or getattr(fn, "__name__", "unknown_tool")

        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            # 1. Check Circuit Breaker before calling
            if circuit_breaker.is_tripped(t_name):
                return (
                    f"[CIRCUIT_BREAKER_OPEN] Tool '{t_name}' is currently paused due to repeated failures. "
                    f"Do not call this tool. {fallback_guidance}"
                )

            try:
                raw_result = fn(*args, **kwargs)
                circuit_breaker.record_success(t_name)
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
                circuit_breaker.record_failure(t_name)
                logger.warning(
                    f"[WARN] Tool '{t_name}' execution shielded from crash: {err_type}: {e}"
                )
                return (
                    f"[ADVISORY] Tool '{t_name}' temporarily unavailable ({err_type}). "
                    f"Do not retry this tool immediately. {fallback_guidance}"
                )

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def shield_crewai_tool(tool_obj: Any, max_chars: int = DEFAULT_MAX_TOOL_CHARS) -> Any:
    """
    Applies pruning, circuit breaking, and error-shielding to a CrewAI Tool / BaseTool or callable.
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
