import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from crew_engine import MarketRoverCrew, create_crew

class TestCrewEngine:
    @pytest.fixture
    def mock_dependencies(self):
        """Mock out all external dependencies"""
        with patch('crew_engine.Crew') as mock_crew, \
             patch('crew_engine.AgentFactory') as mock_agents, \
             patch('crew_engine.TaskFactory') as mock_tasks:
            
            # Setup mocks
            mock_agents.create_all_agents.return_value = {
                'analyst': MagicMock(role='analyst'),
                'researcher': MagicMock(role='researcher')
            }
            mock_tasks.create_all_tasks.return_value = [MagicMock(), MagicMock()]
            
            yield mock_crew, mock_agents, mock_tasks

    def test_startup_initialization(self, mock_dependencies):
        """Test if crew initializes with correct components"""
        mock_crew_cls, mock_agents, mock_tasks = mock_dependencies
        
        crew = MarketRoverCrew()
        
        # Verify factories were called
        mock_agents.create_all_agents.assert_called_once()
        mock_tasks.create_all_tasks.assert_called_once()
        
        # Verify CrewAI initialized correctly
        mock_crew_cls.assert_called_once()
        call_kwargs = mock_crew_cls.call_args[1]
        assert len(call_kwargs['agents']) == 2
        assert len(call_kwargs['tasks']) == 2
        assert call_kwargs['verbose'] is True

    def test_run_execution(self, mock_dependencies):
        """Test the run method execution flow"""
        mock_crew_cls, _, _ = mock_dependencies
        mock_crew_instance = mock_crew_cls.return_value
        mock_crew_instance.kickoff.return_value = "Analysis Results"
        
        crew = MarketRoverCrew()
        result = crew.run()
        
        mock_crew_instance.kickoff.assert_called_once()
        assert result == "Analysis Results"

    def test_error_handling(self, mock_dependencies):
        """Test error handling during execution"""
        mock_crew_cls, _, _ = mock_dependencies
        mock_crew_instance = mock_crew_cls.return_value
        mock_crew_instance.kickoff.side_effect = Exception("API Error")
        
        crew = MarketRoverCrew()
        
        with pytest.raises(Exception) as excinfo:
            crew.run()
        
        assert "API Error" in str(excinfo.value)

    def test_get_crew_info(self, mock_dependencies):
        """Test info retrieval"""
        crew = MarketRoverCrew()
        info = crew.get_crew_info()
        
        assert info['num_agents'] == 2
        assert info['num_tasks'] == 2
        assert info['version'] == '2.0'

    def test_factory_function(self, mock_dependencies):
        """Test the create_crew factory"""
        crew = create_crew()
        assert isinstance(crew, MarketRoverCrew)
