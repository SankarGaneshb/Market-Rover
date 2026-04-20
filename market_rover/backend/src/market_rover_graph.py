from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.agents.retrieval_node import retrieval_node
from src.agents.strategy_node import strategy_node
from src.agents.sentiment_node import sentiment_node
from src.agents.technical_node import technical_node
from src.agents.traditional_node import traditional_node
from src.agents.dividend_node import dividend_node
from src.agents.sector_node import sector_node
from src.agents.shadow_node import shadow_node
from src.agents.forensic_node import forensic_node
from src.agents.reporting_node import reporting_node

def create_market_rover_graph():
    """
    Constructs the Market-Rover Intelligence Graph.
    Implements a non-linear, parallel, and stateful flow.
    """
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("sentiment", sentiment_node)
    workflow.add_node("technicals", technical_node)
    workflow.add_node("traditional", traditional_node)
    workflow.add_node("dividend", dividend_node)
    workflow.add_node("sector", sector_node)
    workflow.add_node("shadow", shadow_node)
    workflow.add_node("forensic", forensic_node)
    workflow.add_node("reporting", reporting_node)

    # 2. Define Edges (The Flow)
    # START -> SETUP
    workflow.add_edge(START, "retrieval")
    workflow.add_edge("retrieval", "strategy")

    # Fan-Out: Parallel execution
    workflow.add_edge("strategy", "sentiment")
    workflow.add_edge("strategy", "technicals")
    workflow.add_edge("strategy", "traditional")
    workflow.add_edge("strategy", "dividend")
    workflow.add_edge("strategy", "sector")
    workflow.add_edge("strategy", "forensic")

    # Fan-In: Wait for all 5 parallel branches to finish
    workflow.add_edge("sentiment", "shadow")
    workflow.add_edge("technicals", "shadow")
    workflow.add_edge("traditional", "shadow")
    workflow.add_edge("dividend", "shadow")
    workflow.add_edge("sector", "shadow")
    workflow.add_edge("forensic", "shadow")

    # Final Sync
    workflow.add_edge("shadow", "reporting")
    workflow.add_edge("reporting", END)

    # 3. Compile
    return workflow.compile()

# Example usage:
# app = create_market_rover_graph()
# config = {"configurable": {"thread_id": "user_session_123"}}
# app.invoke({"tickers": ["TCS.NS", "RELIANCE.NS"], "user_id": "test_user"}, config)
