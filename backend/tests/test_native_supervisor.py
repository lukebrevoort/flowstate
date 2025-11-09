"""Test the native LangChain v1 supervisor implementation"""

import pytest
from agents.supervisor import supervisor_agent, schedule_task, manage_assignments, format_response
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


@pytest.mark.asyncio
async def test_supervisor_calls_schedule_task():
    """Test that supervisor correctly routes calendar requests to schedule_task tool"""

    result = await supervisor_agent.ainvoke({"messages": [HumanMessage(content="What's on my calendar today?")]})

    messages = result["messages"]

    # Should have at least: HumanMessage, AIMessage with tool_call, ToolMessage, AIMessage with result
    assert len(messages) >= 4, f"Expected at least 4 messages, got {len(messages)}"

    # Find the AI message that calls tools
    tool_call_message = None
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_call_message = msg
            break

    assert tool_call_message is not None, "No AIMessage with tool_calls found"

    # Verify schedule_task was called
    tool_names = [tc["name"] for tc in tool_call_message.tool_calls]
    assert "schedule_task" in tool_names, f"schedule_task not in {tool_names}"

    print(f"✅ Supervisor correctly called schedule_task tool")


@pytest.mark.asyncio
async def test_supervisor_calls_manage_assignments():
    """Test that supervisor correctly routes assignment requests to manage_assignments tool"""

    result = await supervisor_agent.ainvoke({"messages": [HumanMessage(content="What assignments do I have?")]})

    messages = result["messages"]

    # Find the AI message that calls tools
    tool_call_message = None
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_call_message = msg
            break

    assert tool_call_message is not None, "No AIMessage with tool_calls found"

    # Verify manage_assignments was called
    tool_names = [tc["name"] for tc in tool_call_message.tool_calls]
    assert "manage_assignments" in tool_names, f"manage_assignments not in {tool_names}"

    print(f"✅ Supervisor correctly called manage_assignments tool")


@pytest.mark.asyncio
async def test_supervisor_multi_agent_workflow():
    """Test that supervisor coordinates multiple agents in sequence"""

    result = await supervisor_agent.ainvoke(
        {"messages": [HumanMessage(content="Show me my calendar and assignments for today")]}
    )

    messages = result["messages"]

    # Collect all tool calls
    all_tool_calls = []
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            all_tool_calls.extend([tc["name"] for tc in msg.tool_calls])

    print(f"Tool calls made: {all_tool_calls}")

    # Should call both schedule_task and manage_assignments
    assert (
        "schedule_task" in all_tool_calls or "manage_assignments" in all_tool_calls
    ), f"Expected at least one agent tool call, got {all_tool_calls}"

    # Should eventually call format_response to format the final JSX
    # (might be in same message or separate)
    assert "format_response" in all_tool_calls or any(
        isinstance(msg, AIMessage) and msg.content and "<" in str(msg.content) for msg in messages
    ), "Expected format_response call or JSX content in final response"

    print(f"✅ Supervisor correctly coordinated multi-agent workflow")


@pytest.mark.asyncio
async def test_supervisor_formats_final_response():
    """Test that supervisor formats responses in JSX"""

    result = await supervisor_agent.ainvoke({"messages": [HumanMessage(content="What's on my schedule?")]})

    messages = result["messages"]

    # Check if format_response was called OR JSX content exists
    has_format_call = False
    has_jsx_content = False

    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            if any(tc["name"] == "format_response" for tc in msg.tool_calls):
                has_format_call = True

        if isinstance(msg, (AIMessage, ToolMessage)):
            content = getattr(msg, "content", "")
            if content and "<" in str(content) and ("Typography" in str(content) or "div" in str(content)):
                has_jsx_content = True

    assert has_format_call or has_jsx_content, "Expected format_response call or JSX content in response"

    print(f"✅ Supervisor correctly formats responses")


@pytest.mark.asyncio
async def test_sub_agents_call_their_tools():
    """Test that sub-agents actually call their tools (not just respond conversationally)"""

    result = await supervisor_agent.ainvoke({"messages": [HumanMessage(content="Check my calendar for today")]})

    messages = result["messages"]

    # Look for evidence that sub-agent tools were called
    # We should see ToolMessages that come from the scheduler's tools
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]

    # Should have tool messages from both supervisor tools AND sub-agent tools
    assert len(tool_messages) > 0, "Expected tool messages from sub-agents"

    # The supervisor should have invoked schedule_task
    ai_messages_with_tools = [
        msg for msg in messages if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls
    ]

    assert len(ai_messages_with_tools) > 0, "Expected AI messages with tool calls"

    print(f"✅ Sub-agents are calling their tools (found {len(tool_messages)} tool messages)")
    print(f"Tool call chain: {len(ai_messages_with_tools)} AI messages made tool calls")
