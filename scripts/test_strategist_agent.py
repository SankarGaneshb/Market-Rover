
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from agents import AgentFactory
from crewai import Task, Crew

def run_test():
    print("🚀 Initializing Market Impact Strategist Check...")
    
    try:
        # 1. Create Agents
        agents = AgentFactory.create_all_agents()
        strategist = agents['news_scraper']  # This is our upgraded "Market Impact Strategist"
        
        print(f"✅ Agent Loaded: {strategist.role}")
        print(f"🛠️  Tools Available: {[t.name for t in strategist.tools]}")
        
        # 2. Define a Test Task
        # We start with a generic task to trigger the tools
        task = Task(
            description=(
                "Analyze the current market situation for 'RELIANCE'. "
                "1. Check Global Cues (Crude Oil impact?). "
                "2. Search for recent big news using the Search Tool. "
                "3. Check for any Official Corporate Actions. "
                "Provide a short strategic summary."
            ),
            agent=strategist,
            expected_output="A brief strategic impact report for RELIANCE."
        )
        
        # 3. Create a Mini-Crew
        crew = Crew(
            agents=[strategist],
            tasks=[task],
            verbose=True
        )
        
        print("\n🌊 Kickoff! Running the agent (this may take 30-60s)...")
        result = crew.kickoff()
        
        print("\n\n" + "="*50)
        print("🎯 FINAL AGENT OUTPUT")
        print("="*50)
        print(result)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
