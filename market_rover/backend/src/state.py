from typing import Annotated, TypedDict, List, Dict, Any, Optional
from operator import add

class AgentState(TypedDict):
    """
    The state of the Market-Rover Intelligence Graph.
    This maintains context across nodes and supports parallel execution.
    """

    # --- Input & Context ---
    tickers: List[str]
    user_id: str
    session_id: str

    # --- Analysis Layer ---
    regime: Optional[str]  # e.g., Goldilocks, Stagflation, etc.
    macro_context: Optional[str]

    # --- Parallel Results (Accumulated) ---
    # Annotated with 'add' to handle results returning from parallel branches
    sentiment_data: Annotated[List[Dict[str, Any]], add]
    technical_data: Annotated[List[Dict[str, Any]], add]
    traditional_insights: Annotated[List[str], add]
    dividend_data: Annotated[List[Dict[str, Any]], add]
    sector_data: Annotated[List[Dict[str, Any]], add]

    # --- Shadow Layer (Forensic Synthesis) ---
    shadow_signals: List[str]
    institutional_intent: str # Accumulation, Distribution, Neutral

    # --- Output Layer ---
    final_report: str
    json_output: Dict[str, Any]

    # --- SRE & Health ---
    errors: Annotated[List[str], add]
    current_node: str
    vulnerability_score: float # Threshold for HIL interrupt

    # --- Interactive UX (Celebrations & Feedback) ---
    # Triggered during specific node successes, not just the end.
    celebrations: Annotated[List[Dict[str, Any]], add]
    feedback_prompts: Annotated[List[Dict[str, Any]], add]

    # --- Memory (LTM) ---
    historical_stances: Dict[str, Any]
