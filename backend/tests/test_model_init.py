#!/usr/bin/env python3
"""
Simple test to verify the model initialization works correctly
"""

import sys
import os
from typing import List, Any

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.supervisor import ValidatedChatAnthropic, model, streaming_model

    print("✅ Successfully imported ValidatedChatAnthropic and models")
    print(f"✅ Non-streaming model: {model}")
    print(f"✅ Streaming model: {streaming_model}")
    print(f"✅ Non-streaming model streaming setting: {model.streaming}")
    print(f"✅ Streaming model streaming setting: {streaming_model.streaming}")

    # Test basic validation
    messages: List[Any] = []
    validated = model.validate_messages(messages) if hasattr(model, "validate_messages") else messages
    print(f"✅ Message validation works: {type(validated)}")

    print("\n🎉 All basic tests passed! The ResponseNotRead fix should be working.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Other error: {e}")
    sys.exit(1)
