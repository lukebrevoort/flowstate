"""
Test LangGraph agents functionality.
"""

import pytest


def test_supervisor_agent_import():
    """Test that the supervisor agent can be imported."""
    try:
        from agents.supervisor import app as agent_app

        assert agent_app is not None, "Agent app should not be None"
    except ImportError as e:
        pytest.fail(f"Failed to import supervisor agent: {e}")


def test_configuration_import():
    """Test that agent configuration can be imported."""
    try:
        import agents.configuration as configuration

        assert configuration is not None
    except ImportError as e:
        pytest.fail(f"Failed to import agent configuration: {e}")


def test_agents_exist():
    """Test that individual agent modules exist."""
    agent_modules = [
        "agents.project_manager",
        "agents.scheduler",
        "agents.response",
        "agents.supervisor",
    ]

    for module_name in agent_modules:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_langgraph_config():
    """Test that langgraph.json configuration is valid."""
    import json
    import os

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "langgraph.json"
    )
    assert os.path.exists(config_path), "langgraph.json should exist"

    with open(config_path, "r") as f:
        config = json.load(f)

    assert "graphs" in config, "Config should have 'graphs' section"
    assert (
        "task_maistro" in config["graphs"]
    ), "Config should define 'task_maistro' graph"
    assert (
        config["graphs"]["task_maistro"] == "agents.supervisor:app"
    ), "Graph should point to supervisor app"


def test_streaming_functionality():
    """Test that streaming functions can be imported."""
    try:
        from agents.supervisor import stream_response, stream_events

        assert stream_response is not None
        assert stream_events is not None
    except ImportError as e:
        pytest.fail(f"Failed to import streaming functions: {e}")


@pytest.mark.asyncio
async def test_agent_basic_functionality():
    """Test basic agent functionality if possible."""
    try:
        from agents.supervisor import app as agent_app

        if agent_app is None:
            pytest.skip("Agent app is None, skipping functionality test")

        # Test that the agent app has expected attributes
        # This is a basic smoke test
        assert hasattr(agent_app, "__call__") or hasattr(
            agent_app, "ainvoke"
        ), "Agent app should be callable or have ainvoke method"

    except Exception as e:
        pytest.fail(f"Agent basic functionality test failed: {e}")
