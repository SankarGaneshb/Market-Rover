import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Force Matplotlib to use non-interactive backend 'Agg' for CI/Headless environments
import matplotlib
matplotlib.use('Agg')

# Mock CrewAI if it fails to import (fixes CI collection errors due to missing system deps for chromadb etc)
try:
    import crewai
    from crewai.tools import tool
except ImportError:
    print("⚠️ CrewAI not found/broken. Mocking for test collection.")
    mock_crewai = MagicMock()
    sys.modules["crewai"] = mock_crewai
    sys.modules["crewai.tools"] = MagicMock()
    sys.modules["crewai.process"] = MagicMock()
    sys.modules["crewai.agent"] = MagicMock()
    sys.modules["crewai.task"] = MagicMock()
    sys.modules["crewai.project"] = MagicMock() # Often imported
    
    # Ensure 'tool' decorator can be imported from crewai.tools
    sys.modules["crewai.tools"].tool = lambda x: x

# Add the project root directory to sys.path
# This ensures that 'rover_tools', 'utils', 'crew_engine', etc. can be imported by tests
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
