from typing import Annotated, Dict, List, Literal, TypedDict
import os
import datetime 

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
    tools_needed: List[str]
    tools_used: List[str]
    task_addressed: bool
    next: Literal["project_manager", "scheduler", "FINISH"]

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-haiku-latest")

# Add this function after the LLM initialization and before the agent nodes
def format_agent_response(result, agent_name):
    """Extract and format agent response with better error handling and metadata"""
    try:
        # Extract output with comprehensive fallback options
        if isinstance(result, dict):
            output = result.get("output") or result.get("content") or str(result)
        elif hasattr(result, "content"):
            output = result.content
        else:
            output = str(result)
        
        # Use improved task completion evaluation
        task_completed = evaluate_task_completion(output, agent_name)
        
        # Create structured message with metadata
        new_message = AIMessage(
            content=output,
            name=agent_name,
            additional_kwargs={
                "complete": task_completed,
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": agent_name,
                "action_taken": "processed_request"
            }
        )
        
        return new_message, task_completed
        
    except Exception as e:
        # Fallback for any errors
        error_msg = f"Error processing {agent_name} response: {str(e)}"
        return AIMessage(content=error_msg, name=f"{agent_name}_error"), False

def identify_tools_needed(messages):
    """Analyze the latest message to determine which tools are needed"""
    # Get the latest user message
    latest_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get("role") == "user"):
            latest_message = msg.content if hasattr(msg, "content") else msg.get("content", "")
            break
    
    if not latest_message:
        return []
    
    # Keywords that indicate which agent might be needed
    project_keywords = ["assignment", "task", "project", "deadline", "work", "todo", "organize", "priority"]
    scheduler_keywords = ["schedule", "calendar", "time", "event", "meeting", "appointment", "exam", "study", "when"]
    
    tools_needed = []
    
    # Simple keyword matching to determine needed tools
    if any(keyword in latest_message.lower() for keyword in project_keywords):
        tools_needed.append("project_manager")
    
    if any(keyword in latest_message.lower() for keyword in scheduler_keywords):
        tools_needed.append("scheduler")
    
    # If the query suggests multiple tools are needed
    combined_indicators = [
        ("assignment", "time"), ("project", "schedule"), ("deadline", "calendar"),
        ("exam", "study"), ("task", "when"), ("work", "time")
    ]
    
    for term1, term2 in combined_indicators:
        if term1 in latest_message.lower() and term2 in latest_message.lower():
            if "project_manager" not in tools_needed:
                tools_needed.append("project_manager")
            if "scheduler" not in tools_needed:
                tools_needed.append("scheduler")
    
    return tools_needed

def supervisor_node(state: State):
    # Get messages with a default empty list if not present
    messages_list = state.get("messages", [])
    
    # Check if the last message is from the user (indicating a new question or follow-up)
    should_reset_task_flag = False
    if messages_list and (
        (isinstance(messages_list[-1], HumanMessage)) or
        (isinstance(messages_list[-1], dict) and messages_list[-1].get("role") == "user") or
        (isinstance(messages_list[-1], str))
    ):
        should_reset_task_flag = True
    
    # Reset task flags if the last message is from the user
    if should_reset_task_flag:
        state["task_addressed"] = False
        state["tools_used"] = []
        # Determine which tools are needed for this new query
        state["tools_needed"] = identify_tools_needed(messages_list)
    
    # If messages list is empty or doesn't contain proper messages,
    # check if there's a 'query' or 'input' field
    if not messages_list:
        query = state.get("query", state.get("input", "How can I help you today?"))
        if isinstance(query, str):
            messages_list = [HumanMessage(content=query)]
            state["tools_needed"] = identify_tools_needed([HumanMessage(content=query)])
    
    # Initialize tools lists if they don't exist
    if "tools_needed" not in state:
        state["tools_needed"] = identify_tools_needed(messages_list)
    if "tools_used" not in state:
        state["tools_used"] = []
    
    # Check if all needed tools have been used
    all_tools_used = all(tool in state["tools_used"] for tool in state["tools_needed"])
    
    # If task has been addressed by required agents and there's no new user question, finish
    if state.get("task_addressed", False) and all_tools_used and not should_reset_task_flag:
        return {"next": "FINISH", "messages": messages_list, "tools_needed": state["tools_needed"], "tools_used": state["tools_used"], "task_addressed": True}
    
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
    
    # Don't finish if there are still tools that need to be used
    if goto == "FINISH" and not all_tools_used:
        # Find next unused needed tool
        for tool in state["tools_needed"]:
            if tool not in state["tools_used"]:
                goto = tool
                break
    
    return {
        "next": goto, 
        "messages": messages_list, 
        "tools_needed": state["tools_needed"], 
        "tools_used": state["tools_used"],
        "task_addressed": state.get("task_addressed", False)
    }

def project_manager_node(state: State):
    """Node for the project manager agent."""
    # Create execution with tools
    project_manager_agent = create_react_agent(
        llm, tools=project_manager_tools,
        prompt=project_manager_prompt,
    )
    
    try:
        # Execute agent with retry capability
        result = project_manager_agent.invoke({"messages": state["messages"]})
        
        # Use enhanced response formatting
        new_message, task_completed = format_agent_response(result, "project_manager")
        
    except Exception as e:
        # Handle any exceptions during agent execution
        error_msg = f"Error in project manager agent: {str(e)}"
        new_message = AIMessage(content=error_msg, name="project_manager_error")
        task_completed = False
    
    # Update conversation history
    messages = state["messages"] + [new_message]
    
    # Mark this tool as used
    tools_used = state.get("tools_used", [])
    if "project_manager" not in tools_used:
        tools_used.append("project_manager")
    
    return {
        "messages": messages, 
        "task_addressed": task_completed or state.get("task_addressed", False),
        "tools_needed": state.get("tools_needed", []),
        "tools_used": tools_used
    }

def scheduler_node(state: State):
    """Node for the scheduler agent."""
    # Create execution with tools
    scheduler_agent = create_react_agent(
        llm, tools=scheduler_tools,
        prompt=scheduler_prompt,
    )
    
    try:
        # Execute agent with retry capability
        result = scheduler_agent.invoke({"messages": state["messages"]})
        
        # Use enhanced response formatting
        new_message, task_completed = format_agent_response(result, "scheduler")
        
    except Exception as e:
        # Handle any exceptions during agent execution
        error_msg = f"Error in scheduler agent: {str(e)}"
        new_message = AIMessage(content=error_msg, name="scheduler_error")
        task_completed = False
    
    # Update conversation history
    messages = state["messages"] + [new_message]
    
    # Mark this tool as used
    tools_used = state.get("tools_used", [])
    if "scheduler" not in tools_used:
        tools_used.append("scheduler")
    
    return {
        "messages": messages, 
        "task_addressed": task_completed or state.get("task_addressed", False),
        "tools_needed": state.get("tools_needed", []),
        "tools_used": tools_used
    }

def router(state: State):
    next_step = state.get("next", "supervisor")
    
    # If next step is FINISH, check if all needed tools have been used
    if next_step == "FINISH":
        tools_needed = state.get("tools_needed", [])
        tools_used = state.get("tools_used", [])
        
        # If there are still unused needed tools, route to supervisor to decide next agent
        if tools_needed and not all(tool in tools_used for tool in tools_needed):
            return "supervisor"
        
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
            # Check for error messages
            if message.name.endswith("_error"):
                return f"⚠️ ERROR ({message.name.replace('_error', '')}): {message.content}"
            
            # Get any additional metadata if available
            metadata = ""
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                if 'complete' in message.additional_kwargs:
                    status = "✅ Complete" if message.additional_kwargs['complete'] else "⏳ Partial"
                    metadata = f" [{status}]"
            
            return f"🤖 {message.name.upper()}{metadata}: {message.content}"
        else:
            return f"🤖 AI: {message.content}"
    return "⚠️ Message format not recognized"

def evaluate_task_completion(output, agent_name):
    """Determine if the agent response indicates task completion."""
    # Basic length check
    if len(output) < 30:
        return False
    
    # Check for error indicators
    error_terms = ["error", "exception", "failed", "couldn't", "unable to"]
    if any(term in output.lower() for term in error_terms):
        return False
    
    # Check for question indicators (suggesting incomplete response)
    if output.count("?") > 2 or output.strip().endswith("?"):
        return False
        
    # Check for completion indicators by agent type
    if agent_name == "project_manager":
        completion_terms = ["added task", "created project", "updated", "organized", 
                           "completed", "task list", "here's your", "finished"]
    elif agent_name == "scheduler":
        completion_terms = ["scheduled", "added to calendar", "time blocked", 
                           "appointment", "meeting set", "event created"]
    else:
        completion_terms = ["completed", "done", "finished", "here's the result"]
    
    # Check if any completion terms are present
    has_completion_term = any(term in output.lower() for term in completion_terms)
    
    # Combine heuristics: sufficient length + completion indicator
    return len(output) > 50 and has_completion_term

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