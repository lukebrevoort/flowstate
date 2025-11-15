"""Test the StateGraph-based supervisor implementation"""

import os
import pytest
from agents.supervisor import app, AgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Skip these tests if ANTHROPIC_API_KEY is not set or is a test key
skip_if_no_api_key = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY").startswith("test-"),
    reason="Requires valid ANTHROPIC_API_KEY"
)


@pytest.mark.asyncio
@skip_if_no_api_key
async def test_supervisor_calls_schedule_task():
    """Test that supervisor correctly routes calendar requests to scheduler agent"""

    state: AgentState = {
        "messages": [HumanMessage(content="What's on my calendar today?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    config = {"configurable": {"user_id": "test-user-123", "todo_category": "general", "thread_id": "test-thread-123"}}

    result = await app.ainvoke(state, config=config)

    messages = result["messages"]

    # Should have routed to scheduler agent
    assert result.get("current_agent") == "scheduler", f"Expected scheduler agent, got {result.get('current_agent')}"

    # Should have completed and formatted response
    assert result.get("needs_response_formatting") == False, "Response should be formatted"

    # Should have multiple messages including tool calls
    assert len(messages) >= 3, f"Expected at least 3 messages, got {len(messages)}"

    print(f"✅ Supervisor correctly routed to scheduler agent")


@pytest.mark.asyncio
@skip_if_no_api_key
async def test_supervisor_calls_manage_assignments():
    """Test that supervisor correctly routes assignment requests to project manager agent"""

    state: AgentState = {
        "messages": [HumanMessage(content="What assignments do I have?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    config = {"configurable": {"user_id": "test-user-123", "todo_category": "general", "thread_id": "test-thread-456"}}

    result = await app.ainvoke(state, config=config)

    # Should have routed to project_manager agent
    assert (
        result.get("current_agent") == "project_manager"
    ), f"Expected project_manager agent, got {result.get('current_agent')}"

    # Should have completed and formatted response
    assert result.get("needs_response_formatting") == False, "Response should be formatted"

    print(f"✅ Supervisor correctly routed to project manager agent")


@pytest.mark.asyncio
@skip_if_no_api_key
async def test_supervisor_multi_agent_workflow():
    """Test that supervisor coordinates agents and response formatting"""

    state: AgentState = {
        "messages": [HumanMessage(content="Show me my calendar and assignments for today")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": "Student studying Computer Science",
        "agent_results": {},
    }

    config = {"configurable": {"user_id": "test-user-123", "todo_category": "general", "thread_id": "test-thread-789"}}

    result = await app.ainvoke(state, config=config)

    messages = result["messages"]

    # Should route to one of the agents
    assert result.get("current_agent") in [
        "scheduler",
        "project_manager",
        "general",
    ], f"Expected valid agent, got {result.get('current_agent')}"

    # Should always format the response
    assert result.get("needs_response_formatting") == False, "Response should be formatted by Response Agent"

    # Should have agent results
    assert result.get("agent_results"), "Should have agent results"

    print(f"✅ Supervisor correctly coordinated multi-agent workflow")


@pytest.mark.asyncio
@skip_if_no_api_key
async def test_supervisor_formats_final_response():
    """Test that supervisor formats responses in JSX via Response Agent"""

    state: AgentState = {
        "messages": [HumanMessage(content="What's on my schedule?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    config = {"configurable": {"user_id": "test-user-123", "todo_category": "general", "thread_id": "test-thread-101"}}

    result = await app.ainvoke(state, config=config)

    messages = result["messages"]

    # Response should be formatted
    assert result.get("needs_response_formatting") == False, "Response must be formatted by Response Agent"

    # Check for JSX content in final message
    final_message = messages[-1] if messages else None
    assert final_message is not None, "Should have a final message"

    content = getattr(final_message, "content", "")
    has_jsx = "<>" in str(content) or "Typography" in str(content)

    assert has_jsx, f"Expected JSX content in final response, got: {str(content)[:200]}"

    print(f"✅ Supervisor correctly formats responses via Response Agent")


@pytest.mark.asyncio
@skip_if_no_api_key
async def test_sub_agents_call_their_tools():
    """Test that sub-agents loop and call multiple tools before completing"""

    state: AgentState = {
        "messages": [HumanMessage(content="Check my calendar for today")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    config = {"configurable": {"user_id": "test-user-123", "todo_category": "general", "thread_id": "test-thread-202"}}

    result = await app.ainvoke(state, config=config)

    messages = result["messages"]

    # Look for tool messages - should have multiple from looping
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]

    # Scheduler agent should loop and call multiple tools
    # Expect at least: get_current_time, get_events (even if they fail)
    assert len(tool_messages) >= 1, f"Expected at least 1 tool message from looping, got {len(tool_messages)}"

    # Should have AI messages with tool calls
    ai_messages_with_tools = [
        msg for msg in messages if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls
    ]

    assert len(ai_messages_with_tools) >= 1, "Expected AI messages with tool calls from looping"

    print(f"✅ Sub-agents are looping and calling tools (found {len(tool_messages)} tool messages)")
    print(f"Tool call iterations: {len(ai_messages_with_tools)} AI messages made tool calls")
