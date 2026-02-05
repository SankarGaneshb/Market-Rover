import sys
import os
from pathlib import Path

# Add the project root directory to sys.path
# This ensures that 'rover_tools', 'utils', 'crew_engine', etc. can be imported by tests
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
