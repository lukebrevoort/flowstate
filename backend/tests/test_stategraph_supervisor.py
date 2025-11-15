"""
Test the new StateGraph-based supervisor implementation
"""

import pytest
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from agents.supervisor import app, create_flowstate_graph, AgentState, supervisor_node, _validate_jsx


def test_graph_structure():
    """Test that the graph has the correct structure"""
    graph = create_flowstate_graph()

    # Verify graph was compiled
    assert graph is not None
    print("✅ Graph compiled successfully")


def test_jsx_validation():
    """Test JSX validation function"""
    # Valid JSX
    valid_jsx = """<>
    <Typography variant="h1" className="text-blue-500">Hello</Typography>
    </>"""
    assert _validate_jsx(valid_jsx) == True

    # Invalid JSX - missing fragment
    invalid_jsx1 = """<Typography variant="h1">Hello</Typography>"""
    assert _validate_jsx(invalid_jsx1) == False

    # Invalid JSX - no Typography
    invalid_jsx2 = """<>
    <div>Hello</div>
    </>"""
    assert _validate_jsx(invalid_jsx2) == False

    # Invalid JSX - unmatched tags
    invalid_jsx3 = """<>
    <Typography variant="h1">Hello
    </>"""
    assert _validate_jsx(invalid_jsx3) == False

    print("✅ JSX validation working correctly")


@pytest.mark.asyncio
async def test_supervisor_routing_scheduler():
    """Test that supervisor correctly routes to scheduler"""
    state: AgentState = {
        "messages": [HumanMessage(content="What's on my calendar tomorrow?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": "Student studying Computer Science",
        "agent_results": {},
    }

    result = await supervisor_node(state)

    # Should route to scheduler
    assert result["current_agent"] == "scheduler"
    assert result["needs_response_formatting"] == True
    print(f"✅ Supervisor routed calendar query to: {result['current_agent']}")


@pytest.mark.asyncio
async def test_supervisor_routing_project_manager():
    """Test that supervisor correctly routes to project manager"""
    state: AgentState = {
        "messages": [HumanMessage(content="Show me my assignments for this week")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": "Student studying Computer Science",
        "agent_results": {},
    }

    result = await supervisor_node(state)

    # Should route to project_manager
    assert result["current_agent"] == "project_manager"
    assert result["needs_response_formatting"] == True
    print(f"✅ Supervisor routed assignment query to: {result['current_agent']}")


@pytest.mark.asyncio
async def test_supervisor_routing_general():
    """Test that supervisor correctly routes general queries"""
    state: AgentState = {
        "messages": [HumanMessage(content="Hello, how are you?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    result = await supervisor_node(state)

    # Should route to general
    assert result["current_agent"] == "general"
    assert result["needs_response_formatting"] == True
    print(f"✅ Supervisor routed general query to: {result['current_agent']}")


@pytest.mark.asyncio
async def test_full_graph_execution():
    """Test the complete graph execution flow"""
    # Initial state
    initial_state: AgentState = {
        "messages": [HumanMessage(content="Hello! What can you help me with?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": "Student studying Computer Science",
        "agent_results": {},
    }

    # Configure the run
    config = {"configurable": {"user_id": "test-user-123", "todo_category": "general", "thread_id": "test-thread-123"}}

    # Run the graph
    result = await app.ainvoke(initial_state, config=config)

    # Verify result structure
    assert "messages" in result
    assert len(result["messages"]) > 1  # Should have user message + responses
    assert result["needs_response_formatting"] == False  # Should be marked complete

    # Find the final response
    final_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
    assert len(final_messages) > 0, "Should have at least one AI response"

    final_response = final_messages[-1].content
    print(f"\n✅ Full graph execution completed")
    print(f"📝 Final response preview: {str(final_response)[:200]}...")

    # Check if it's formatted (should have JSX elements)
    # Note: This is a general query so response might vary
    assert final_response is not None and len(str(final_response)) > 0


@pytest.mark.asyncio
async def test_response_agent_always_runs():
    """Test that Response Agent always runs at the end"""
    initial_state: AgentState = {
        "messages": [HumanMessage(content="What's my schedule?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    config = {"configurable": {"user_id": "test-user-123", "todo_category": "general", "thread_id": "test-thread-456"}}

    result = await app.ainvoke(initial_state, config=config)

    # Response formatting should be marked as complete
    assert result["needs_response_formatting"] == False, "Response Agent must run and mark formatting complete"

    print("✅ Response Agent enforcement verified")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING NEW STATEGRAPH-BASED SUPERVISOR")
    print("=" * 80 + "\n")

    # Run synchronous tests
    print("Test 1: Graph Structure")
    test_graph_structure()

    print("\nTest 2: JSX Validation")
    test_jsx_validation()

    print("\nTest 3: Supervisor Routing - Scheduler")
    asyncio.run(test_supervisor_routing_scheduler())

    print("\nTest 4: Supervisor Routing - Project Manager")
    asyncio.run(test_supervisor_routing_project_manager())

    print("\nTest 5: Supervisor Routing - General")
    asyncio.run(test_supervisor_routing_general())

    # Run async tests
    print("\nTest 6: Full Graph Execution")
    asyncio.run(test_full_graph_execution())

    print("\nTest 7: Response Agent Enforcement")
    asyncio.run(test_response_agent_always_runs())

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80 + "\n")
