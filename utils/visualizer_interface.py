import sys
import os
from pathlib import Path

# Add parent directory to path to allow imports from root
sys.path.append(str(Path(__file__).parent.parent))

from agents import create_visualizer_agent
from tasks import create_market_snapshot_task
from crewai import Crew, Process
from config import GOOGLE_API_KEY

def check_environment():
    """Check if environment is properly configured."""
    if not GOOGLE_API_KEY:
        return False, "GOOGLE_API_KEY not found in environment variables."
    return True, ""

def generate_market_snapshot(ticker):
    """
    Runs the Visualizer Agent for a specific ticker.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'SBIN')
        
    Returns:
        dict: Contains 'success' (bool), 'message' (str), 'image_path' (str or None)
    """
    # Check environment
    is_valid, error_msg = check_environment()
    if not is_valid:
        return {
            "success": False,
            "message": error_msg,
            "image_path": None
        }
    
    try:
        # Create Agent and Task
        agent = create_visualizer_agent()
        task = create_market_snapshot_task(agent, ticker)
        
        # Create Crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        # Run the crew
        result = crew.kickoff()
        
        # Determine image path
        # The tool saves it to output/{ticker}_snapshot.png
        # We need to verify it exists
        output_dir = Path("output")
        image_path = output_dir / f"{ticker}_report.pdf"
        
        if image_path.exists():
            return {
                "success": True,
                "message": str(result),
                "image_path": str(image_path)
            }
        else:
            return {
                "success": True, # Task finished but image might be missing?
                "message": str(result) + "\n\nWarning: Image file not found.",
                "image_path": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error running visualizer: {str(e)}",
            "image_path": None
        }
