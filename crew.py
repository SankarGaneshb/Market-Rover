"""
Crew configuration for Market-Rover 2.0
Orchestrates all agents and tasks using CrewAI with parallel execution support.
"""
from crewai import Crew, Process
from agents import AgentFactory
from tasks import TaskFactory
from config import MAX_ITERATIONS, MAX_PARALLEL_STOCKS, RATE_LIMIT_DELAY
from typing import Optional, Callable

# Structured logging and metrics
from utils.logger import logger
from utils.metrics import track_error_detail


class MarketRoverCrew:
    """Market-Rover 2.0 intelligence crew with parallel execution."""
    
    def __init__(self, max_parallel_stocks: Optional[int] = None, 
                 progress_callback: Optional[Callable] = None):
        """
        Initialize the crew with all agents and tasks.
        
        Args:
            max_parallel_stocks: Maximum number of stocks to process in parallel (default: from config)
            progress_callback: Optional callback function for progress updates (percentage, stock_name, status)
        """
        # Create all agents
        self.agents = AgentFactory.create_all_agents()
        
        # Create all tasks with dependencies
        self.tasks = TaskFactory.create_all_tasks(self.agents)
        
        # Set parallel execution parameters
        self.max_parallel_stocks = max_parallel_stocks or MAX_PARALLEL_STOCKS
        self.progress_callback = progress_callback
        
        # Create the crew
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,  # Tasks still execute in order, but stock processing is parallel
            verbose=True,
            max_rpm=20,  # Rate limiting for API calls
            manager_llm=None,  # Disable manager LLM to avoid OpenAI requirement
        )
    
    def run(self):
        """
        Execute the Market-Rover 2.0 workflow with parallel stock processing.
        
        Returns:
            Final report from the crew
        """
        logger.info("🚀 Starting Market-Rover 2.0 Intelligence Analysis...")
        logger.info(f"⚡ Parallel Mode: Processing up to {self.max_parallel_stocks} stocks concurrently")
        logger.info("%s", "=" * 60)
        
        try:
            # Kick off the crew (parallel processing handled within tasks)
            result = self.crew.kickoff()

            logger.info("%s", "\n" + "=" * 60)
            logger.info("✅ Analysis Complete!")

            return result

        except Exception as e:
            # Log & persist detailed error information for daily triage
            logger.exception("Error during crew execution: %s", str(e))
            try:
                track_error_detail(
                    error_type="CrewExecutionError",
                    message=str(e),
                    context={
                        'max_parallel_stocks': self.max_parallel_stocks,
                        'num_agents': len(self.agents),
                    },
                    user_id=None,
                )
            except Exception:
                logger.debug("Failed to persist crew error detail")
            raise
    
    def get_crew_info(self):
        """Get information about the crew composition."""
        info = {
            'num_agents': len(self.agents),
            'num_tasks': len(self.tasks),
            'process': 'Parallel',
            'max_parallel_stocks': self.max_parallel_stocks,
            'max_iterations': MAX_ITERATIONS,
            'agents': list(self.agents.keys()),
            'version': '2.0'
        }
        return info


def create_crew(max_parallel_stocks: Optional[int] = None, 
                progress_callback: Optional[Callable] = None):
    """
    Factory function to create a new MarketRoverCrew instance.
    
    Args:
        max_parallel_stocks: Maximum number of stocks to process in parallel
        progress_callback: Optional callback for progress updates
        
    Returns:
        MarketRoverCrew instance configured for parallel execution
    """
    return MarketRoverCrew(max_parallel_stocks, progress_callback)
