from agents.orchestrator import run_orchestrator
import json

def test_graph():
    """
    Test the LangGraph setup with the orchestrator and project manager subgraph.
    """
    print("Testing LangGraph orchestrator with project manager...")
    
    # Test with a project-related query
    test_message = "I need to create a new assignment for my Biology class due next Friday at 5pm"
    
    # Run the orchestrator with the test message
    result = run_orchestrator(test_message)
    
    # Print the result in a readable format
    print("\nResult from orchestrator:")
    print("Messages:")
    for message in result["messages"]:
        print(f"  {message.type}: {message.content[:100]}...")
    
    if "agent_outputs" in result:
        print("\nAgent outputs:")
        for agent, output in result["agent_outputs"].items():
            print(f"  {agent}: {output[:100]}...")
    
    return result

if __name__ == "__main__":
    test_graph()