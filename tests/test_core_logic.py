
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch

import pytest
import importlib
from unittest.mock import MagicMock, patch

def test_rover_agents_initialization():
    # Test that agents are created with correct config
    
    # 1. Reload first to get fresh module
    import agents
    importlib.reload(agents)
    
    # 2. Patch the objects inside the 'agents' module
    # We use 'agents.Agent' because that's the reference used inside the module code
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"}), \
         patch('agents.Agent') as MockAgent, \
         patch('agents.LLM') as MockLLM, \
         patch('agents.get_gemini_llm') as MockGetLLM, \
         patch('agents.get_flash_llm') as MockFlashLLM:
        
        from agents import AgentFactory
        
        agents_dict = AgentFactory.create_all_agents()
        
        # Verify Portfolio Manager creation
        pm_call = None
        for call in MockAgent.mock_calls:
            if call.kwargs.get('role') == 'Portfolio Manager':
                pm_call = call
                break
        
        assert pm_call is not None
        assert pm_call.kwargs['allow_delegation'] is False
        assert pm_call.kwargs['verbose'] is True
        
        # Verify Shadow Analyst creation
        sa_call = None
        for call in MockAgent.mock_calls:
            if call.kwargs.get('role') == 'Institutional Shadow Analyst':
                sa_call = call
                break
                
        assert sa_call is not None
        assert len(sa_call.kwargs['tools']) > 0

def test_task_creation():
    # Mock an agent object
    mock_agent = MagicMock()
    mock_agent.role = "Test Agent"
    
    with patch('crewai.Task') as MockTask:
        import tasks
        importlib.reload(tasks)
        from tasks import create_portfolio_retrieval_task
        
        # Task 1
        create_portfolio_retrieval_task(mock_agent)
        
        assert MockTask.called
        call_args = MockTask.call_args
        assert call_args.kwargs['agent'] == mock_agent
        assert "portfolio" in call_args.kwargs['description'].lower()

def test_task_factory_logic():
    # Test high level factory
    # We need to mock the agents dict
    agents_map = {
        'portfolio_manager': MagicMock(),
        'news_scraper': MagicMock(),
        'sentiment_analyzer': MagicMock(),
        'market_context': MagicMock(),
        'shadow_analyst': MagicMock(),
        'report_generator': MagicMock(),
        'visualizer': MagicMock()
    }
    
    # Patch first so reload picks up the mocks
    with patch('tasks.create_portfolio_retrieval_task') as mock_create, \
         patch('crewai.Task') as MockTask:
        
        # Reload tasks to ensure it uses the patched Class/Functions
        import tasks
        importlib.reload(tasks)
        from tasks import TaskFactory
        
        tasks_list = TaskFactory.create_all_tasks(agents_map)
        
        # Verify result
        assert isinstance(tasks_list, list)
        assert len(tasks_list) > 0
