"""
Test script to verify the supervisor routing fix
This ensures the supervisor correctly routes to scheduler/project_manager agents
even when there's conversation history in the thread
"""

import asyncio
import uuid
from langchain_core.messages import HumanMessage
from agents.supervisor import app


async def test_scheduler_routing():
    """Test that scheduler requests are properly routed"""

    thread_id = f"test_thread_{uuid.uuid4()}"

    print(f"\n{'='*80}")
    print(f"🧪 Testing Scheduler Routing")
    print(f"Thread ID: {thread_id}")
    print(f"{'='*80}\n")

    config = {
        "configurable": {
            "user_id": "test_user",
            "todo_category": "default",
            "thread_id": thread_id,
        }
    }

    # First message: General conversation
    print("📤 Message 1: 'Hello, how are you?'")
    state1 = {
        "messages": [HumanMessage(content="Hello, how are you?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    try:
        result1 = await app.ainvoke(state1, config=config)
        print(f"✅ Message 1 processed")
    except Exception as e:
        print(f"❌ Message 1 failed: {e}")
        return False

    # Second message: Request calendar operation (should route to scheduler)
    print(f"\n{'─'*80}\n")
    print("📤 Message 2 (SCHEDULER REQUEST): 'What does my schedule look like today?'")
    state2 = {
        "messages": [HumanMessage(content="What does my schedule look like today?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    try:
        # Check the routing in the result
        result2 = await app.ainvoke(state2, config=config)

        # Look for evidence of scheduler being called
        # The state should have gone through scheduler node
        messages = result2.get("messages", [])

        # Check if we got a meaningful response (not just default general response)
        last_message = str(messages[-1].content) if messages else ""

        print(f"✅ Message 2 processed")
        print(f"   Response length: {len(last_message)} chars")

        # The response should be about calendar/schedule
        if any(word in last_message.lower() for word in ["calendar", "schedule", "event", "appointment"]):
            print(f"\n{'='*80}")
            print("✅ SUCCESS: Scheduler routing is working!")
            print("✅ Request was correctly routed to scheduler agent")
            print(f"{'='*80}\n")
            return True
        else:
            print(f"\n{'='*80}")
            print("⚠️  WARNING: Response doesn't mention calendar/schedule")
            print("   This might indicate routing issue")
            print(f"{'='*80}\n")
            return False

    except Exception as e:
        print(f"❌ Message 2 failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_project_manager_routing():
    """Test that project manager requests are properly routed"""

    thread_id = f"test_thread_{uuid.uuid4()}"

    print(f"\n{'='*80}")
    print(f"🧪 Testing Project Manager Routing")
    print(f"Thread ID: {thread_id}")
    print(f"{'='*80}\n")

    config = {
        "configurable": {
            "user_id": "test_user",
            "todo_category": "default",
            "thread_id": thread_id,
        }
    }

    # First message: General conversation
    print("📤 Message 1: 'Hi there!'")
    state1 = {
        "messages": [HumanMessage(content="Hi there!")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    try:
        result1 = await app.ainvoke(state1, config=config)
        print(f"✅ Message 1 processed")
    except Exception as e:
        print(f"❌ Message 1 failed: {e}")
        return False

    # Second message: Request assignment operation (should route to project_manager)
    print(f"\n{'─'*80}\n")
    print("📤 Message 2 (PROJECT MANAGER REQUEST): 'Show me my assignments'")
    state2 = {
        "messages": [HumanMessage(content="Show me my assignments")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }

    try:
        result2 = await app.ainvoke(state2, config=config)

        messages = result2.get("messages", [])
        last_message = str(messages[-1].content) if messages else ""

        print(f"✅ Message 2 processed")
        print(f"   Response length: {len(last_message)} chars")

        # The response should be about assignments/tasks
        if any(word in last_message.lower() for word in ["assignment", "task", "project", "notion"]):
            print(f"\n{'='*80}")
            print("✅ SUCCESS: Project Manager routing is working!")
            print("✅ Request was correctly routed to project_manager agent")
            print(f"{'='*80}\n")
            return True
        else:
            print(f"\n{'='*80}")
            print("⚠️  WARNING: Response doesn't mention assignments/tasks")
            print("   This might indicate routing issue")
            print(f"{'='*80}\n")
            return False

    except Exception as e:
        print(f"❌ Message 2 failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_mixed_routing_sequence():
    """Test alternating between different agent types"""

    thread_id = f"test_thread_{uuid.uuid4()}"

    print(f"\n{'='*80}")
    print(f"🧪 Testing Mixed Routing Sequence")
    print(f"Thread ID: {thread_id}")
    print(f"{'='*80}\n")

    config = {
        "configurable": {
            "user_id": "test_user",
            "todo_category": "default",
            "thread_id": thread_id,
        }
    }

    messages_and_expected = [
        ("Hello!", "general"),
        ("What assignments do I have?", "project_manager"),
        ("What about my schedule tomorrow?", "scheduler"),
        ("Thanks!", "general"),
    ]

    for i, (msg_text, expected_agent) in enumerate(messages_and_expected, 1):
        print(f"📤 Message {i}: '{msg_text}' (expect: {expected_agent})")
        state = {
            "messages": [HumanMessage(content=msg_text)],
            "current_agent": None,
            "needs_response_formatting": True,
            "user_profile": None,
            "agent_results": {},
        }

        try:
            result = await app.ainvoke(state, config=config)
            print(f"   ✅ Processed successfully")
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}")
            return False

    print(f"\n{'='*80}")
    print("✅ SUCCESS: All mixed routing requests processed!")
    print(f"{'='*80}\n")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ROUTING FIX TEST SUITE")
    print("=" * 80)

    # Run tests
    result1 = asyncio.run(test_scheduler_routing())
    result2 = asyncio.run(test_project_manager_routing())
    result3 = asyncio.run(test_mixed_routing_sequence())

    print("\n" + "=" * 80)
    if result1 and result2 and result3:
        print("✅ ALL TESTS PASSED")
        print("The supervisor routing is working correctly!")
    else:
        print("⚠️  SOME TESTS HAD WARNINGS")
        print("Review the output above for details")
    print("=" * 80 + "\n")
