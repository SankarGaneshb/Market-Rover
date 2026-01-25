import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from agents import AgentFactory
    print("Attempting to create all agents...")
    agents = AgentFactory.create_all_agents()
    print("Successfully created all agents:")
    for name, agent in agents.items():
        print(f" - {name}: OK")
    print("\nVERIFICATION SUCCESSFUL")
except Exception as e:
    print(f"\nVERIFICATION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
