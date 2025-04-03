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

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from IPython.display import display, Image

from project_manager import prompt as project_manager_prompt, tools as project_manager_tools
from scheduler_agent import prompt as scheduler_prompt, tools as scheduler_tools

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
    " task and respond with their results and status. Only run again if the result is incomplete or if the next worker is required to continue the conversation.\n"
    " When finished, respond with FINISH."
)

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["project_manager", "scheduler", "FINISH"]


llm = ChatAnthropic(model="claude-3-5-haiku-latest")

class State(MessagesState):
    next: str


def supervisor_node(state: State) -> Command[Literal["project_manager", "scheduler", "__end__"]]:
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
        
        return Command(
            update={"messages": [HumanMessage(content=result["output"], name="project_manager")]},
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

    
    return Command(
        update={"messages": [HumanMessage(content=output, name="scheduler")]},
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
user_query = "What do I have going on tommorrow?"
print(f"\n👤 User: {user_query}\n")

# Track the agents we've seen respond
# Replace the streaming loop with this better version
for step in graph.stream(
    {"messages": [HumanMessage(content=user_query)]}, subgraphs=True
):
    if len(step) != 2:
        continue
    
    node_name, state = step
    
    # DEBUG: Print what we received at each step
    print(f"Step: {node_name}")
    if "messages" in state and state["messages"]:
        print(f"Latest message type: {type(state['messages'][-1])}")
        if hasattr(state["messages"][-1], "name"):
            print(f"Latest message name: {state['messages'][-1].name}")
    
    # Show supervisor routing separately from agent responses
    if node_name == "supervisor" and state.get("next"):
        print(f"🧠 Supervisor routing to: {state['next']}")
    
    # Extract and display agent responses - don't track seen responses by name
    if "messages" in state and len(state["messages"]) > 0:
        latest_msg = state["messages"][-1]
        
        if hasattr(latest_msg, "name"):
            if latest_msg.name == "scheduler":
                print(f"\n📅 Scheduler:\n{latest_msg.content}\n")
            elif latest_msg.name == "project_manager":
                print(f"\n📋 Project Manager:\n{latest_msg.content}\n")







