import pytest
import os
import json
from unittest.mock import MagicMock, patch
from rover_tools.memory_tool import save_prediction_tool, read_past_predictions_tool, MEMORY_FILE_PATH
from tasks import TaskFactory

@pytest.fixture
def clean_memory():
    """Backup and restore memory file."""
    if os.path.exists(MEMORY_FILE_PATH):
        with open(MEMORY_FILE_PATH, 'r') as f:
            backup = f.read()
    else:
        backup = None
        
    yield
    
    # Restore
    if backup:
        with open(MEMORY_FILE_PATH, 'w') as f:
            f.write(backup)
    elif os.path.exists(MEMORY_FILE_PATH):
        os.remove(MEMORY_FILE_PATH)

def invoke_tool(tool_obj, **kwargs):
    """Helper to invoke tool whether it's a function or StructredTool."""
    if hasattr(tool_obj, 'run'):
        return tool_obj.run(**kwargs)
    elif callable(tool_obj):
        return tool_obj(**kwargs)
    else:
        # Pydantic check?
        return tool_obj.func(**kwargs)

def test_memory_tool_read_write(clean_memory):
    """Test saving and reading predictions."""
    # Write
    # CrewAI tools take a single string argument if simple, or dict? 
    # Our tools define typed args. CrewAI decorators usually wrap them.
    # We'll try passing arguments as a dict or directly depending on implementation.
    
    # Try calling via helper
    # save_prediction_tool(ticker="TEST.NS", signal="Buy", confidence="High")
    res = invoke_tool(save_prediction_tool, ticker="TEST.NS", signal="Buy", confidence="High")
    assert "Saved prediction" in res
    
    # Read
    res_read = invoke_tool(read_past_predictions_tool, ticker="TEST.NS")
    assert "TEST.NS" in res_read or "Memory Recall" in res_read
    assert "Buy" in res_read
    
    # Read nonexistent
    res_none = invoke_tool(read_past_predictions_tool, ticker="FAKE.NS")
    assert "No past history" in res_none

def test_shadow_task_memory_prompt():
    """Verify Shadow Task has memory instructions."""
    # Mock agents and tasks same as before
    mock_agents = {
        'portfolio_manager': MagicMock(),
        'news_scraper': MagicMock(),
        'sentiment_analyzer': MagicMock(),
        'market_context': MagicMock(),
        'shadow_analyst': MagicMock(),
        'report_generator': MagicMock(),
        'visualizer': MagicMock()
    }
    
    # Create tasks
    # We rely on dynamic import or similar if we want to avoid the Pydantic error again
    # But since we fixed tests/test_prompt_logic.py by mocking Task, let's reuse that strategy here strictly for prompt checking
    # Or actually, we can just inspect the creating function directly if we import it
    
    from tasks import create_shadow_analysis_task
    
    # Create a dummy agent just to pass to the function (if it checks type)
    # But create_shadow_analysis_task expects 'agent' and 'context'
    
    agent = MagicMock()
    context = []
    
    # We'll use a patch to mock Task class to avoid validation
    with patch('tasks.Task') as MockTask:
        MockTask.return_value.description = "Captured"
        
        # We need to capture the description passed TO the constructor
        create_shadow_analysis_task(agent, context)
        
        # Check call args
        args, kwargs = MockTask.call_args
        description = kwargs.get('description', '')
        
        assert "MEMORY CHECK" in description
        assert "read_past_predictions_tool" in description
        assert "save_prediction_tool" in description

if __name__ == "__main__":
    pytest.main([__file__])
