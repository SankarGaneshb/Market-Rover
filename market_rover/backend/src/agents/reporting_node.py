import os
from src.state import AgentState
from src.utils.db_manager import db
from src.utils.logger import get_logger
import json

logger = get_logger(__name__)

async def reporting_node(state: AgentState) -> dict:
    """
    Node: Intelligence Synthesis & Reporting
    The final point of the graph. Compiles all data into a cohesive report.
    Triggers the 'Final Success' celebration and feedback loops.
    """
    logger.info("Executing Reporting Node...")

    regime = state.get("regime", "NEUTRAL")
    shadow_signals = state.get("shadow_signals", [])
    intent = state.get("institutional_intent", "NEUTRAL")

    # 1. Compile Final Report
    report_title = f"Market-Rover Intelligence Report: {regime} Protocol"
    signals_text = "\n".join([f"- {s}" for s in shadow_signals]) if shadow_signals else "No major divergences detected."

    final_report = f"""
# {report_title}
## Institutional Stance: {intent}

### Macro Summary
{state.get('macro_context', 'No macro context available.')}

### Technical & Fundamental Hygiene
- Technical Status: {json.dumps(state.get('technical_data', []), indent=2)}
- Fundamental Ratios: {json.dumps(state.get('fundamental_data', []), indent=2)}
- Dividend Yields: {json.dumps(state.get('dividend_data', []), indent=2)}

### Sector Rotation & Alpha Discovery
{json.dumps(state.get('sector_data', []), indent=2)}

### Forensic Signals (Shadow Analyst)
{signals_text}

### Auspicious Timing (Traditional)
{state.get('traditional_insights', ['No traditional data available.'])[0]}

---
*Disclaimer: AI-generated analysis is for informational purposes only.*
"""

    # 2. Interactive UX Trigger: Final Success
    celebrations = [{
        "type": "FINAL_CONFETTI_BURST",
        "message": "Analysis Complete! Your institutional intelligence report is ready.",
        "context": "report_ready"
    }]

    # 3. Interactive UX Trigger: Final Feedback
    feedback_prompts = [{
        "type": "RATE_REPORT",
        "message": "How helpful was this specific analysis? (Selecting a reaction improves my future accuracy).",
        "choices": ["Stellar", "Helpful", "Standard", "Needs Work"]
    }]

    # 4. Long-Term Memory (LTM) Storage
    user_handle = state.get("discoverable_handle", "anonymous_user")
    tickers = state.get("tickers", [])

    await db.connect()
    for ticker in tickers:
        # Save the unified stance for this session
        await db.store_memory(
            user_handle=user_handle,
            ticker=ticker,
            stance=intent,
            logic=f"Analyzed in {regime} regime. Forensic Signals: {len(shadow_signals)} detected."
        )

    # Log the activity
    await db.log_activity(user_handle, "GENERATED_INTEL_REPORT")

    return {
        "final_report": final_report,
        "celebrations": celebrations,
        "feedback_prompts": feedback_prompts,
        "current_node": "reporting"
    }
