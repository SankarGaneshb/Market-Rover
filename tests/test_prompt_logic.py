import pytest
from unittest.mock import MagicMock, patch
import tasks

@pytest.fixture
def mock_task_class():
    """Mock crewai.Task to avoid Pydantic validation."""
    with patch('tasks.Task') as MockTask:
        # Arrange: When Task() is called, return an object that stores the inputs
        def side_effect(**kwargs):
            mock_obj = MagicMock()
            mock_obj.description = kwargs.get('description', '')
            mock_obj.agent = kwargs.get('agent')
            return mock_obj
        
        MockTask.side_effect = side_effect
        yield MockTask

@pytest.fixture
def mock_agents():
    """Create simple mock agents."""
    return {
        'portfolio_manager': MagicMock(),
        'news_scraper': MagicMock(),
        'sentiment_analyzer': MagicMock(),
        'market_context': MagicMock(),
        'shadow_analyst': MagicMock(),
        'report_generator': MagicMock(),
        'visualizer': MagicMock()
    }

def test_strategist_regime_logic(mock_task_class, mock_agents):
    """Verify Strategist task contains Regime Branching logic."""
    tasks.TaskFactory.create_all_tasks(mock_agents)
    
    # We need to find the call that corresponds to the Strategist Task
    # Strategist is creating task2
    # The calls to Task() happen 6 times.
    # We can inspect the calls to find the one for Strategist.
    
    found = False
    for call in mock_task_class.call_args_list:
        kwargs = call.kwargs
        description = kwargs.get('description', '')
        if "REGIME CHECK" in description:
            found = True
            assert "IF VIX > 22" in description
            assert "DECLARE REGIME: DEFENSIVE" in description
    
    assert found, "Strategist Task with Regime Logic not found in Task() calls."

def test_technical_regime_logic(mock_task_class, mock_agents):
    """Verify Technical Analyst adapts to Regime."""
    tasks.TaskFactory.create_all_tasks(mock_agents)
    
    found = False
    for call in mock_task_class.call_args_list:
        kwargs = call.kwargs
        description = kwargs.get('description', '')
        if "DYNAMIC TOOL USAGE" in description:
             if "IF REGIME = DEFENSIVE" in description:
                found = True
                assert "IGNORE all 'Breakout' signals" in description
    
    assert found, "Technical Task with Regime Logic not found."

def test_report_tone_logic(mock_task_class, mock_agents):
    """Verify Report Generator adapts tone to Regime."""
    tasks.TaskFactory.create_all_tasks(mock_agents)
    
    found = False
    for call in mock_task_class.call_args_list:
        kwargs = call.kwargs
        description = kwargs.get('description', '')
        if "Step 1: **Check REGIME**" in description:
            found = True
            assert "Tone must be Cautious" in description
    
    assert found, "Report Task with Tone Logic not found."

