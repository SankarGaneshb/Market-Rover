import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Force Matplotlib to use non-interactive backend 'Agg' for CI/Headless environments
import matplotlib
matplotlib.use('Agg')

# Mock Heavy/Missing Dependencies for CI
# This prevents crashes when transitive deps (like chromadb) are missing
# but the main package (crewai) is installed.
MOCK_MODULES = [
    'chromadb',
    'chromadb.config', 
    'pysqlite3',
    'docling',
    'langchain_community.vectorstores',
    'embedchain'
]

for mod_name in MOCK_MODULES:
    try:
        __import__(mod_name)
    except ImportError:
        # Only mock if strictly missing/broken
        # (check sys.modules just in case it was half-loaded)
        if mod_name not in sys.modules:
            sys.modules[mod_name] = MagicMock()

# Mock CrewAI specifically if it's broken (e.g. checks for chromadb at runtime)
# We wrap this in a generally broad try/except to catch ANY initialization error
try:
    import crewai
    from crewai.tools import tool
except Exception: # Catch ImportError AND runtime errors (like missing sqlite binary)
    print("⚠️ CrewAI broken/missing. Mocking for test collection.")
    mock_crewai = MagicMock()
    sys.modules["crewai"] = mock_crewai
    sys.modules["crewai.tools"] = MagicMock()
    sys.modules["crewai.process"] = MagicMock()
    sys.modules["crewai.agent"] = MagicMock()
    sys.modules["crewai.task"] = MagicMock()
    sys.modules["crewai.project"] = MagicMock()
    
    # Ensure 'tool' decorator works
    sys.modules["crewai.tools"].tool = lambda x: x

# Add the project root directory to sys.path
# This ensures that 'rover_tools', 'utils', 'crew_engine', etc. can be imported by tests
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
