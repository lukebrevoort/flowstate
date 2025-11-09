#!/usr/bin/env python3
"""
Debug script to see message sequences
"""
import asyncio
from agents.supervisor import stream_response


async def debug_messages():
    config = {"configurable": {"thread_id": "debug-thread-001"}}
    test_input = "Show me my schedule"

    print("Starting debug stream...")
    print("=" * 80)

    chunk_count = 0
    try:
        async for chunk in stream_response(test_input, config):
            chunk_count += 1
            print(f"\n{'='*80}")
            print(f"CHUNK #{chunk_count} YIELDED TO FRONTEND:")
            print(f"  Type: {chunk.get('type')}")
            print(f"  Agent: {chunk.get('agent')}")
            print(f"  Message: {chunk.get('message', '')[:80]}")
            if "content" in chunk:
                content_preview = str(chunk.get("content", ""))[:200]
                print(f"  Content: {content_preview}...")
            print(f"{'='*80}\n")

            # Stop after 15 chunks to see Response Agent
            if chunk_count >= 15:
                print("Stopping after 15 chunks...")
                break

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n✅ Received {chunk_count} total chunks")


if __name__ == "__main__":
    asyncio.run(debug_messages())
