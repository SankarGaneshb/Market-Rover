
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch

# Mock CrewAI components BEFORE importing agents/tasks
# This prevents actual API calls or model initialization during import
sys.modules['crewai'] = MagicMock()
sys.modules['crewai.tools'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()

# Now import the modules to test
# We need to ensure that when they import Agent/Task, they get our mocks
with patch('crewai.Agent') as MockAgent, \
     patch('crewai.Task') as MockTask, \
     patch('langchain_google_genai.ChatGoogleGenerativeAI') as MockLLM:
    
    from agents import AgentFactory
    from tasks import (
        create_portfolio_retrieval_task,
        create_market_strategy_task,
        create_sentiment_analysis_task,
        create_technical_analysis_task,
        create_shadow_analysis_task,
        create_report_generation_task,
        create_market_snapshot_task
    )


def test_rover_agents_initialization():
    # Test that agents are created with correct config
    # We patch agents.Agent to intercept calls
    with patch('agents.Agent') as MockAgent, \
         patch('agents.get_gemini_llm') as MockLLM:
        agents = AgentFactory.create_all_agents()
        
        # Verify Portfolio Manager creation
        # We search through the calls to find the one for Portfolio Manager
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
    
    # Task 1
    t1 = create_portfolio_retrieval_task(mock_agent)
    # The result t1 is a Mock object (MockTask return value).
    # We can check if MockTask was called with correct args.
    
    # However, since create_portfolio_retrieval_task returns Task(...), 
    # t1 IS the return value of MockTask().
    # If we want to check what arguments were passed to Task(), we need to inspect MockTask.
    
    # But for simplicity, let's verify MockTask was called.
    assert MockTask.called
    
    call_args = MockTask.call_args
    assert call_args.kwargs['agent'] == mock_agent
    assert "portfolio" in call_args.kwargs['description'].lower()

def test_task_factory_logic():
    # Test high level factory
    # We need to mock the agents dict
    agents = {
        'portfolio_manager': MagicMock(),
        'news_scraper': MagicMock(),
        'sentiment_analyzer': MagicMock(),
        'market_context': MagicMock(),
        'shadow_analyst': MagicMock(),
        'report_generator': MagicMock()
    }
    
    from tasks import TaskFactory
    with patch('tasks.create_portfolio_retrieval_task') as mock_create:
        tasks = TaskFactory.create_all_tasks(agents)
        assert len(tasks) == 6
