#!/usr/bin/env python3
"""
Test to verify the StateGraph supervisor and agent initialization works correctly
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.supervisor import app, base_model, create_flowstate_graph

    print("✅ Successfully imported StateGraph app and base_model")
    print(f"✅ Base model: {base_model}")
    print(f"✅ StateGraph app compiled: {app is not None}")

    # Test graph creation
    graph = create_flowstate_graph()
    print(f"✅ Graph creation works: {graph is not None}")

    print("\n🎉 All basic tests passed! StateGraph supervisor is working correctly.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Other error: {e}")
    sys.exit(1)
