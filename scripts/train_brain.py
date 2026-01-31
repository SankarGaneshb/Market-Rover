"""
Train Brain - Nifty 50 Batch Analyzer.

This script runs the Market Rover Crew on the entire Nifty 50 universe (via NiftyTop20.csv) to:
1. Generate market insights.
2. Populate the 'Agent Brain' with predictions (for future learning).
3. "Train" the system by building a history of successes/failures.

Usage:
    python scripts/train_brain.py
"""
import sys
import os
import shutil
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from crew_engine import create_crew
from utils.logger import get_logger
from config import PORTFOLIO_FILE, PROJECT_ROOT

logger = get_logger(__name__)

TRAINING_SOURCE = PROJECT_ROOT / "NiftyTop20.csv"
LIVE_PORTFOLIO = PROJECT_ROOT / PORTFOLIO_FILE
BACKUP_PORTFOLIO = PROJECT_ROOT / f"{PORTFOLIO_FILE}.bak"

def main():
    logger.info("🧠 Starting Nifty 50 Brain Training...")
    
    if not TRAINING_SOURCE.exists():
        logger.error(f"Training source {TRAINING_SOURCE} not found. Please create it first.")
        return

    # 1. Swap Portfolio (Safe Backup)
    logger.info(f"Swapping {LIVE_PORTFOLIO.name} with {TRAINING_SOURCE.name}...")
    
    # Backup existing
    if LIVE_PORTFOLIO.exists():
        shutil.copy2(LIVE_PORTFOLIO, BACKUP_PORTFOLIO)
    
    # Copy training data to live slot
    shutil.copy2(TRAINING_SOURCE, LIVE_PORTFOLIO)
    
    try:
        # 2. Initialize Crew
        crew = create_crew(max_parallel_stocks=10)
        
        # 3. Run Analysis
        logger.info("🚀 Kicking off Agent Workflow on Nifty Top 20...")
        result = crew.run()
        
        logger.info("✅ Training Run Complete.")
        logger.info("Predictions have been saved to memory.json")
        logger.info("Run 'python scripts/validate_outcomes.py' after 3-7 days to close the loop.")
        
    except Exception as e:
        logger.exception("Training failed")
        
    finally:
        # 4. Restore Original Portfolio
        logger.info("Restoring original user portfolio...")
        if BACKUP_PORTFOLIO.exists():
            shutil.move(BACKUP_PORTFOLIO, LIVE_PORTFOLIO)
            # LIVE_PORTFOLIO now contains original user data
        else:
            # If no backup existed (first run?), just clean up
            if LIVE_PORTFOLIO.exists():
                 os.remove(LIVE_PORTFOLIO)
                 
        logger.info("System restoration complete.")

if __name__ == "__main__":
    main()
