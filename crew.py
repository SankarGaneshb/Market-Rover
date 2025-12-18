"""
Crew configuration for Market Rover system.
Orchestrates all agents and tasks using CrewAI.
"""
from crewai import Crew, Process
from agents import AgentFactory
from tasks import TaskFactory
from config import MAX_ITERATIONS


class MarketRoverCrew:
    """Market Rover intelligence crew."""
    
    def __init__(self):
        """Initialize the crew with all agents and tasks."""
        # Create all agents
        self.agents = AgentFactory.create_all_agents()
        
        # Create all tasks with dependencies
        self.tasks = TaskFactory.create_all_tasks(self.agents)
        
        # Create the crew
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,  # Execute tasks in order
            verbose=True,
            max_rpm=10,  # Rate limiting for API calls
            manager_llm=None,  # Disable manager LLM to avoid OpenAI requirement
        )
    
    def run(self):
        """
        Execute the Market Rover workflow.
        
        Returns:
            Final report from the crew
        """
        print("🚀 Starting Market Rover Intelligence Analysis...")
        print("=" * 60)
        
        try:
            # Kick off the crew
            result = self.crew.kickoff()
            
            print("\n" + "=" * 60)
            print("✅ Analysis Complete!")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Error during crew execution: {str(e)}")
            raise
    
    def get_crew_info(self):
        """Get information about the crew composition."""
        info = {
            'num_agents': len(self.agents),
            'num_tasks': len(self.tasks),
            'process': 'Sequential',
            'max_iterations': MAX_ITERATIONS,
            'agents': list(self.agents.keys())
        }
        return info


def create_crew():
    """Factory function to create a new MarketRoverCrew instance."""
    return MarketRoverCrew()
