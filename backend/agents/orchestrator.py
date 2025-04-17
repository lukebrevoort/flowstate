from typing import Annotated, Dict, List, Literal, TypedDict
import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from IPython.display import display, Image

from agents.project_manager import prompt as project_manager_prompt, tools as project_manager_tools
from agents.scheduler_agent import prompt as scheduler_prompt, tools as scheduler_tools

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from anthropic._exceptions import OverloadedError
import json

# Create a retry decorator for Anthropic API calls
@retry(
    retry=retry_if_exception_type(OverloadedError),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5)
)
def invoke_with_retry(llm, messages, **kwargs):
    return llm.invoke(messages, **kwargs)

members = ["project_manager", "scheduler"]
options = members + ["FINISH"]

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status.\n\n"
    "EFFICIENCY GUIDELINES:\n"
    "- Route to project_manager for assignment and task management questions\n"
    "- Route to scheduler for calendar events and time management questions\n"
    "- Respond with FINISH immediately when ANY of these conditions are met:\n"
    "  1. An agent has provided a complete answer to the user's question\n"
    "  2. The necessary information has been retrieved and presented\n"
    "  3. The requested action has been successfully completed\n"
    "- NEVER route to an agent just to summarize or explain another agent's response\n"
    "- NEVER alternate between agents more than once unless absolutely necessary\n\n"
    "Token efficiency is critical. Respond with FINISH as soon as the task is complete."
)

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal["project_manager", "scheduler", "FINISH"]

# Define our state
class State(TypedDict):
    messages: List[BaseMessage]
    next: str
    task_addressed: bool

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-haiku-latest")

def supervisor_node(state: State):
    # If task has been addressed by one of the agents, consider finishing
    if state.get("task_addressed", False):
        return {"next": "FINISH"}
    
    # Get messages with a default empty list if not present
    messages_list = state.get("messages", [])
    
    # If messages list is empty or doesn't contain proper messages,
    # check if there's a 'query' or 'input' field
    if not messages_list:
        query = state.get("query", state.get("input", "How can I help you today?"))
        if isinstance(query, str):
            messages_list = [HumanMessage(content=query)]
    
    # Format messages for Claude
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Add user messages in the right format
    for msg in messages_list:
        if isinstance(msg, dict):
            messages.append(msg)
        elif isinstance(msg, BaseMessage):
            # Convert LangChain message to dict format
            role = "user" if msg.type == "human" else "assistant"
            messages.append({"role": role, "content": msg.content})
        elif isinstance(msg, str):
            # Handle raw string input
            messages.append({"role": "user", "content": msg})
    
    # Ensure we have at least one user message
    if len(messages) == 1:  # Only system message
        messages.append({"role": "user", "content": "How can I help you today?"})
    
    # Use the retry wrapper
    response = invoke_with_retry(llm.with_structured_output(Router), messages)
    goto = response["next"]
    
    return {"next": goto, "messages": messages_list}

def project_manager_node(state: State):
    """Node for the project manager agent."""
    # Create execution with tools
    project_manager_agent = create_react_agent(
        llm, tools=project_manager_tools,
        prompt=project_manager_prompt,
    )
    
    result = project_manager_agent.invoke({"messages": state["messages"]})

    output = result.get("output") if isinstance(result, dict) and "output" in result else result.content if hasattr(result, "content") else str(result)

    # Check if result seems complete
    task_completed = len(output) > 50  # Simple heuristic
    
    # Update messages and task status
    new_message = AIMessage(content=output, name="project_manager")
    messages = state["messages"] + [new_message]
    
    return {"messages": messages, "task_addressed": task_completed}

def scheduler_node(state: State):
    """Node for the scheduler agent."""
    # Create execution with tools
    scheduler_agent = create_react_agent(
        llm, tools=scheduler_tools,
        prompt=scheduler_prompt,
    )
    
    result = scheduler_agent.invoke({"messages": state["messages"]})

    output = result.get("output") if isinstance(result, dict) and "output" in result else result.content if hasattr(result, "content") else str(result)

    task_completed = len(output) > 50  # Simple heuristic
    
    # Update messages and task status
    new_message = AIMessage(content=output, name="scheduler")
    messages = state["messages"] + [new_message]
    
    return {"messages": messages, "task_addressed": task_completed}

def router(state: State):
    next_step = state.get("next", "supervisor")
    if next_step == "FINISH":
        return END
    return next_step

# Build the graph
builder = StateGraph(State)

# Add nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("project_manager", project_manager_node) 
builder.add_node("scheduler", scheduler_node)

# Add conditional edges
builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", router)
builder.add_edge("project_manager", "supervisor")
builder.add_edge("scheduler", "supervisor")

# Compile the graph
graph = builder.compile()

# Run the Agents
def format_message(message):
    if hasattr(message, 'content'):
        try:
            # Attempt to parse JSON content
            parsed_content = json.loads(message.content)
            formatted_content = json.dumps(parsed_content, indent=2)
            return f"🤖 AI (Structured Response):\n```json\n{formatted_content}\n```"
        except json.JSONDecodeError:
            # Fallback to plain text formatting
            pass
        
        if message.type == "human":
            return f"👤 USER: {message.content}"
        elif hasattr(message, 'name') and message.name:
            return f"🤖 {message.name.upper()}: {message.content}"
        else:
            return f"🤖 AI: {message.content}"
    return "⚠️ Message format not recognized"

def run_conversation(query):
    """Run the agent conversation with a specific query"""
    print("\n=== Starting Agent Conversation ===\n")
    steps = graph.stream(
        {
            "messages": [HumanMessage(content=query)],
            "task_addressed": False
        }
    )
    
    for step in steps:
        # Extract messages
        if "messages" in step:
            if isinstance(step["messages"], list) and len(step["messages"]) > 0:
                latest_message = step["messages"][-1]
                print(format_message(latest_message))
        
        # Show routing information
        if "next" in step:
            next_agent = step["next"]
            if next_agent != "FINISH":
                print(f"\n→ Routing to: {next_agent}\n")
            else:
                print("\n→ Task complete, finishing conversation\n")
        
        print("----")

# Example usage
if __name__ == "__main__":
    # Use non-relative imports when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.project_manager import prompt as project_manager_prompt, tools as project_manager_tools
    from agents.scheduler_agent import prompt as scheduler_prompt, tools as scheduler_tools
    
    query = "Find some time tonight and tomorrow that so I can finish my Upcoming CS135 Assignments"
    run_conversation(query)