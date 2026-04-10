import sys
import os

# Ensure 'src' is importable when running pytest from this directory
# This is needed because tests use `from src.data.scoring import ...`
sys.path.insert(0, os.path.dirname(__file__))
