from typing import Annotated
import os

from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from typing import Literal
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState, END
from langgraph.types import Command
import json

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from IPython.display import display, Image

from .project_manager import prompt as project_manager_prompt, tools as project_manager_tools
from .scheduler_agent import prompt as scheduler_prompt, tools as scheduler_tools

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from anthropic._exceptions import OverloadedError

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


llm = ChatAnthropic(model="claude-3-5-haiku-latest")

class State(MessagesState):
    next: str
    task_addressed: bool = False


def supervisor_node(state: State) -> Command[Literal["project_manager", "scheduler", "__end__"]]:
    # If task has been addressed by one of the agents, consider finishing
    if state.get("task_addressed", False):
        return Command(goto=END, update={"next": "FINISH"})
    
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    # Use the retry wrapper
    response = invoke_with_retry(llm.with_structured_output(Router), messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto})
    


project_manager_agent = create_react_agent(
    llm, tools=project_manager_tools,
    prompt=project_manager_prompt,)

def project_manager_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the project manager agent."""
    # Create execution with tools
    result = project_manager_agent.invoke({"messages": state["messages"]})
    

    output = result.get("output") if isinstance(result, dict) and "output" in result else result.content if hasattr(result, "content") else str(result)

    # Check if result seems complete
    task_completed = len(output) > 50  # Simple heuristic

    
    return Command(
        update={
            "messages": [HumanMessage(content=output, name="project_manager")],
            "task_addressed": task_completed
        },
        goto="supervisor"
    )


scheduler_agent = create_react_agent(
        llm, tools=scheduler_tools,
        prompt=scheduler_prompt,
    )

def scheduler_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the scheduler agent."""
    # Create execution with tools
    result = scheduler_agent.invoke({"messages": state["messages"]})

    output = result.get("output") if isinstance(result, dict) and "output" in result else result.content if hasattr(result, "content") else str(result)

    task_completed = len(output) > 50  # Simple heuristic

    return Command(
        update={
            "messages": [HumanMessage(content=output, name="scheduler")],
            "task_addressed": task_completed  # Simple heuristic to determine if the task was addressed
            },
        goto="supervisor"
    )

builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("project_manager", project_manager_node)
builder.add_node("scheduler", scheduler_node)
graph = builder.compile()

# Visualize the graph
"""
display(Image(graph.get_graph().draw_mermaid_png()))

graph_png = graph.get_graph().draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(graph_png)
os.system("open graph.png")
"""

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
            "messages": [
                HumanMessage(content=query)
            ]
        },
        subgraphs=True,
    )
    
    for step in steps:
        # Extract subgraph information
        if "subgraph" in step:
            print(f"\n=== Subgraph: {step['subgraph']} ===\n")

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







