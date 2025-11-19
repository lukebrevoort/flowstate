"""
Test script to verify conversation persistence with checkpointer
This demonstrates that the agent can remember context within a thread
"""

import asyncio
import uuid
from langchain_core.messages import HumanMessage
from agents.supervisor import app


async def test_conversation_persistence():
    """Test that the agent remembers context within a thread"""
    
    # Create a unique thread ID for this conversation
    thread_id = f"test_thread_{uuid.uuid4()}"
    
    print(f"\n{'='*80}")
    print(f"🧪 Testing Conversation Persistence")
    print(f"Thread ID: {thread_id}")
    print(f"{'='*80}\n")
    
    # Configuration with thread_id for persistence
    config = {
        "configurable": {
            "user_id": "test_user",
            "todo_category": "default",
            "thread_id": thread_id,
        }
    }
    
    # First message: Ask the agent to remember something
    print("📤 Message 1: 'My favorite color is blue'")
    state1 = {
        "messages": [HumanMessage(content="My favorite color is blue. Please remember this.")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    
    result1 = await app.ainvoke(state1, config=config)
    last_message1 = result1["messages"][-1]
    print(f"🤖 Response 1: {last_message1.content[:200]}...")
    
    # Second message: Ask about previous context (follow-up question)
    print(f"\n{'─'*80}\n")
    print("📤 Message 2: 'What is my favorite color?'")
    state2 = {
        "messages": [HumanMessage(content="What is my favorite color?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    
    result2 = await app.ainvoke(state2, config=config)
    last_message2 = result2["messages"][-1]
    print(f"🤖 Response 2: {last_message2.content[:200]}...")
    
    # Check if the agent remembered the color
    response_content = str(last_message2.content).lower()
    if "blue" in response_content:
        print(f"\n{'='*80}")
        print("✅ SUCCESS: Agent remembered the conversation context!")
        print("✅ The checkpointer is working correctly!")
        print(f"{'='*80}\n")
        return True
    else:
        print(f"\n{'='*80}")
        print("❌ FAILURE: Agent did not remember the conversation context")
        print("❌ The checkpointer may not be configured correctly")
        print(f"{'='*80}\n")
        return False


async def test_multiple_threads():
    """Test that different threads maintain separate contexts"""
    
    print(f"\n{'='*80}")
    print(f"🧪 Testing Multiple Thread Isolation")
    print(f"{'='*80}\n")
    
    # Thread 1: Favorite color is red
    thread_id_1 = f"test_thread_1_{uuid.uuid4()}"
    config_1 = {
        "configurable": {
            "user_id": "test_user",
            "todo_category": "default",
            "thread_id": thread_id_1,
        }
    }
    
    print(f"Thread 1 ({thread_id_1[:20]}...)")
    print("📤 Message: 'My favorite color is red'")
    state_1 = {
        "messages": [HumanMessage(content="My favorite color is red. Remember this.")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    await app.ainvoke(state_1, config=config_1)
    
    # Thread 2: Favorite color is green
    thread_id_2 = f"test_thread_2_{uuid.uuid4()}"
    config_2 = {
        "configurable": {
            "user_id": "test_user",
            "todo_category": "default",
            "thread_id": thread_id_2,
        }
    }
    
    print(f"\nThread 2 ({thread_id_2[:20]}...)")
    print("📤 Message: 'My favorite color is green'")
    state_2 = {
        "messages": [HumanMessage(content="My favorite color is green. Remember this.")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    await app.ainvoke(state_2, config=config_2)
    
    # Ask thread 1 about its color
    print(f"\n{'─'*80}\n")
    print(f"Thread 1 - Ask: 'What is my favorite color?'")
    state_1_query = {
        "messages": [HumanMessage(content="What is my favorite color?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    result_1 = await app.ainvoke(state_1_query, config=config_1)
    response_1 = str(result_1["messages"][-1].content).lower()
    
    # Ask thread 2 about its color
    print(f"Thread 2 - Ask: 'What is my favorite color?'")
    state_2_query = {
        "messages": [HumanMessage(content="What is my favorite color?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    result_2 = await app.ainvoke(state_2_query, config=config_2)
    response_2 = str(result_2["messages"][-1].content).lower()
    
    # Verify thread isolation
    print(f"\n{'='*80}")
    if "red" in response_1 and "green" in response_2:
        print("✅ SUCCESS: Threads maintain separate contexts!")
        print(f"✅ Thread 1 remembered: red")
        print(f"✅ Thread 2 remembered: green")
    else:
        print("❌ FAILURE: Thread isolation may not be working correctly")
        print(f"Thread 1 response: {response_1[:100]}")
        print(f"Thread 2 response: {response_2[:100]}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CONVERSATION PERSISTENCE TEST SUITE")
    print("="*80)
    
    # Run tests
    asyncio.run(test_conversation_persistence())
    asyncio.run(test_multiple_threads())
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80 + "\n")
