#!/usr/bin/env python3
"""
Quick test to see all streaming debug output
"""
import asyncio
import sys
from agents.supervisor import stream_response


async def test_streaming():
    message = "What's on my calendar today?"

    config = {
        "configurable": {
            "user_id": "test_user_123",
            "todo_category": "General",
            "thread_id": "test_thread_123",
        }
    }

    print("Starting stream test...")
    print("=" * 80)

    count = 0
    async for chunk in stream_response(message, config):
        count += 1
        print(f"\n🎉 FRONTEND WOULD RECEIVE CHUNK #{count}:")
        print(f"   Type: {chunk.get('type')}")
        print(f"   Agent: {chunk.get('agent')}")
        print(f"   Message: {chunk.get('message', '')[:100]}")
        if "content" in chunk:
            print(f"   Content length: {len(str(chunk.get('content', '')))}")
            print(f"   Content preview: {str(chunk.get('content', ''))[:150]}...")
        print("-" * 80)

    print(f"\n✅ Test complete! Received {count} chunks total")


if __name__ == "__main__":
    asyncio.run(test_streaming())
