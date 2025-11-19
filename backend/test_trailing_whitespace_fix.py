"""
Test script to verify the trailing whitespace fix
This simulates the exact scenario that caused the error in production
"""

import asyncio
import uuid
from langchain_core.messages import HumanMessage
from agents.supervisor import app


async def test_follow_up_message_with_trailing_whitespace():
    """
    Test that follow-up messages work even when previous messages
    have trailing whitespace (which would have caused the Anthropic error)
    """
    
    # Create a unique thread ID for this conversation
    thread_id = f"test_thread_{uuid.uuid4()}"
    
    print(f"\n{'='*80}")
    print(f"🧪 Testing Follow-Up Message with Trailing Whitespace Fix")
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
    
    # First message: Create a scenario
    print("📤 Message 1: 'I have an assignment called PA6 due tomorrow'")
    state1 = {
        "messages": [HumanMessage(content="I have an assignment called PA6 due tomorrow")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    
    try:
        result1 = await app.ainvoke(state1, config=config)
        print(f"✅ Message 1 processed successfully")
        last_message1 = result1["messages"][-1]
        print(f"   Response length: {len(str(last_message1.content))} chars")
        
        # Check if the response has trailing whitespace (it might)
        content1 = str(last_message1.content)
        if content1.endswith(('\n', ' ', '\t')):
            print(f"   ⚠️  Response has trailing whitespace: {repr(content1[-5:])}")
        
    except Exception as e:
        print(f"❌ Message 1 failed: {e}")
        return False
    
    # Second message: Follow-up (this would have failed before the fix)
    print(f"\n{'─'*80}\n")
    print("📤 Message 2 (FOLLOW-UP): 'Can you schedule time to work on it?'")
    state2 = {
        "messages": [HumanMessage(content="Can you schedule time to work on it?")],
        "current_agent": None,
        "needs_response_formatting": True,
        "user_profile": None,
        "agent_results": {},
    }
    
    try:
        result2 = await app.ainvoke(state2, config=config)
        print(f"✅ Message 2 processed successfully")
        last_message2 = result2["messages"][-1]
        print(f"   Response length: {len(str(last_message2.content))} chars")
        
        print(f"\n{'='*80}")
        print("✅ SUCCESS: Follow-up message worked!")
        print("✅ The trailing whitespace fix is working correctly!")
        print("✅ Anthropic API error has been resolved!")
        print(f"{'='*80}\n")
        return True
        
    except Exception as e:
        error_message = str(e)
        if "trailing whitespace" in error_message.lower():
            print(f"\n{'='*80}")
            print("❌ FAILURE: Trailing whitespace error still occurring")
            print(f"Error: {error_message}")
            print(f"{'='*80}\n")
        else:
            print(f"\n{'='*80}")
            print(f"❌ FAILURE: Different error occurred")
            print(f"Error: {error_message}")
            print(f"{'='*80}\n")
        return False


async def test_multiple_follow_ups():
    """Test multiple follow-up messages in sequence"""
    
    print(f"\n{'='*80}")
    print(f"🧪 Testing Multiple Follow-Up Messages")
    print(f"{'='*80}\n")
    
    thread_id = f"test_thread_{uuid.uuid4()}"
    config = {
        "configurable": {
            "user_id": "test_user",
            "todo_category": "default",
            "thread_id": thread_id,
        }
    }
    
    messages = [
        "I need to study for my exam",
        "When is a good time to study?",
        "Can you block off 3 hours tomorrow?",
        "What time did you schedule it for?"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"📤 Message {i}: '{msg}'")
        state = {
            "messages": [HumanMessage(content=msg)],
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
    print("✅ SUCCESS: All follow-up messages processed successfully!")
    print(f"{'='*80}\n")
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TRAILING WHITESPACE FIX TEST SUITE")
    print("="*80)
    
    # Run tests
    result1 = asyncio.run(test_follow_up_message_with_trailing_whitespace())
    result2 = asyncio.run(test_multiple_follow_ups())
    
    print("\n" + "="*80)
    if result1 and result2:
        print("✅ ALL TESTS PASSED")
        print("The Anthropic trailing whitespace error has been fixed!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80 + "\n")
