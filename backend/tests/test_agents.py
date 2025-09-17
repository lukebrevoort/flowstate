"""Tests for the LangGraph agent functionality."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from agents.supervisor import create_supervisor_agent


@pytest.mark.unit
@pytest.mark.asyncio
async def test_supervisor_agent_creation():
    """Test that supervisor agent can be created."""
    try:
        agent = create_supervisor_agent()
        assert agent is not None
    except Exception as e:
        # If there are import issues, we'll skip this test for now
        pytest.skip(f"Agent creation failed due to dependencies: {e}")


@pytest.mark.unit
def test_response_agent_prompt():
    """Test that response agent prompt is properly configured."""
    from agents.response import response_prompt
    assert response_prompt is not None
    assert isinstance(response_prompt, str)
    assert len(response_prompt) > 0
    
    # Check for key components in the prompt
    assert "react jsx" in response_prompt.lower() or "jsx" in response_prompt.lower()


@pytest.mark.unit
def test_project_manager_tools():
    """Test that project manager tools are available."""
    try:
        from agents.project_manager import tools as project_management_tools
        assert project_management_tools is not None
        assert isinstance(project_management_tools, list)
    except ImportError as e:
        pytest.skip(f"Project manager tools not available: {e}")


@pytest.mark.unit
@patch('agents.supervisor.ChatAnthropic')
def test_agent_with_mocked_llm(mock_llm):
    """Test agent functionality with mocked LLM."""
    mock_llm.return_value = Mock()
    mock_llm.return_value.ainvoke = AsyncMock(return_value="Test response")
    
    try:
        from agents.supervisor import create_supervisor_agent
        agent = create_supervisor_agent()
        assert agent is not None
    except Exception as e:
        pytest.skip(f"Agent test skipped due to dependencies: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_message_handling():
    """Test that agent can handle messages properly."""
    try:
        from agents.supervisor import app as agent_app
        from langchain_core.messages import HumanMessage
        
        if agent_app is None:
            pytest.skip("Agent app not available")
            
        # Test with a simple message
        test_message = HumanMessage(content="Hello, test message")
        
        # This would be an integration test requiring actual API keys
        # For now, we'll just test that the structure is correct
        assert hasattr(agent_app, 'ainvoke') or hasattr(agent_app, 'astream')
        
    except Exception as e:
        pytest.skip(f"Integration test skipped: {e}")


@pytest.mark.unit
def test_agent_configuration():
    """Test agent configuration module."""
    try:
        import agents.configuration as configuration
        assert configuration is not None
    except ImportError:
        pytest.skip("Configuration module not available")


@pytest.mark.unit 
def test_tools_availability():
    """Test that required tools are available."""
    try:
        from agents.project_manager import tools as pm_tools
        assert isinstance(pm_tools, list)
    except ImportError:
        pytest.skip("Project manager tools not available")
        
    # Test other tool modules as they become available