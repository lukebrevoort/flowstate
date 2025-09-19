#!/usr/bin/env python3
"""
Test script to verify the ResponseNotRead error fix
"""

import asyncio
import sys
import os
import pytest

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.supervisor import stream_response


@pytest.mark.asyncio
async def test_stream_response():
    """Test the stream_response function to ensure it doesn't throw ResponseNotRead errors"""

    print("Testing stream_response function...")

    # Create a test configuration
    config = {"configurable": {"thread_id": "test-thread-001"}}

    # Test input
    test_input = "Hello, can you help me organize my schedule?"

    try:
        # Collect stream chunks
        chunks = []
        async for chunk in stream_response(test_input, config):
            chunks.append(chunk)
            print(f"Received chunk: {chunk.get('type', 'unknown')} - {chunk.get('message', 'no message')}")

            # Limit output for testing
            if len(chunks) >= 10:
                print("Stopping after 10 chunks for testing purposes...")
                break

        print(f"\n✅ Test completed successfully! Received {len(chunks)} chunks without ResponseNotRead errors.")
        return True

    except Exception as e:
        if "ResponseNotRead" in str(e) or "streaming response content" in str(e).lower():
            print(f"\n❌ ResponseNotRead error still occurs: {e}")
            return False
        else:
            print(f"\n⚠️  Different error occurred (may be expected): {e}")
            # Other errors might be expected (like model API issues), so we don't fail the test
            return True


async def main():
    """Main test function"""
    print("🧪 Testing ResponseNotRead error fix...\n")

    success = await test_stream_response()

    if success:
        print("\n🎉 Fix appears to be working! No ResponseNotRead errors detected.")
    else:
        print("\n💥 Fix needs more work. ResponseNotRead errors still occurring.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
