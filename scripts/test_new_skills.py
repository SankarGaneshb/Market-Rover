"""Test script to verify agent instantiation and skill assignment."""
from agents import AgentFactory
from rover_tools.advanced_skills import calculate_portfolio_risk_tool

def test_skills():
    print("Testing Agent Factory...")
    agents = AgentFactory.create_all_agents()
    
    print(f"Successfully loaded {len(agents)} agents.")
    for key, agent in agents.items():
        tools_str = [t.name for t in agent.tools] if agent.tools else "None"
        print(f" - {key} ({agent.role}): Tools -> {tools_str}")
        
    print("\nTesting standalone tool execution (Calculate Risk)...")
    res = calculate_portfolio_risk_tool.invoke('{"ticker": "RELIANCE.NS"}')
    print(f"Tool Result: {res}")
    
    print("\nTest Complete! All agents and new tools are properly initialized.")

if __name__ == "__main__":
    test_skills()
