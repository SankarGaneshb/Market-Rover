import os
from src.state import AgentState
from rover_tools.global_market_tool import get_global_cues_data
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def strategy_node(state: AgentState) -> dict:
    """
    Node: Market Strategy
    Maps the 'Quadratic Regime' (Goldilocks/Reflation/Stagflation/Deflation).
    Triggers 'Wow Factor' celebrations for positive regime breakthroughs.
    """
    logger.info("Executing Strategy Node...")

    # 1. Macro Analysis Logic (Quadratic Mapping)
    try:
        # Calls the data-driven function to get VIX, DXY, 10Y Yields
        macro_cues = get_global_cues_data()
        vix = macro_cues.get('vix', 20)
        dxy = macro_cues.get('dxy', 100)
        yield_10y = macro_cues.get('yield_10y', 3.5)
    except Exception as e:
        logger.error(f"Strategy Node Error: {e}")
        return {"errors": ["Macro data currently unavailable."]}

    # 2. Logic: Identify the Quadrant
    regime = "NEUTRAL"
    celebrations = []
    feedback_prompts = []

    if vix < 18 and yield_10y < 4.0:
        regime = "GOLDILOCKS"
        celebrations.append({
            "type": "GLOW_SUCCESS",
            "message": "BREAKTHROUGH: Market conditions have signaled a GOLDILOCKS regime! Time for aggressive tech accumulation.",
            "context": "regime_goldilocks"
        })
    elif vix > 25:
        regime = "DEFLATIONARY / PANIC"
        feedback_prompts.append({
            "type": "RISK_ALERT",
            "message": "ALERT: High VIX Detected. My strategy has shifted to DEFENSIVE. Do you want to hedge your portfolio?",
            "data": {"vix": vix, "suggested": "Cash/Bonds"}
        })
    else:
        regime = "REFLATION / GROWTH"
        celebrations.append({
            "type": "PULSE_ACTION",
            "message": f"Regime: REFLATION. Macro cues are steady. DXY is at {dxy}.",
            "context": "regime_reflation"
        })

    # 3. Strategy Synthesis
    macro_context = (
        f"The market is currently in a {regime} regime. "
        f"VIX is {vix}, suggesting moderate to high conviction for current price action."
    )

    # 4. Interactive UX Trigger: User Consent on Strategy
    feedback_prompts.append({
        "type": "CONFIRM_STRATEGY",
        "message": f"Do you agree with the {regime} assessment? (Your choice impacts my next analysis nodes).",
        "data": {"regime": regime}
    })

    return {
        "regime": regime,
        "macro_context": macro_context,
        "celebrations": celebrations,
        "feedback_prompts": feedback_prompts,
        "current_node": "strategy"
    }
