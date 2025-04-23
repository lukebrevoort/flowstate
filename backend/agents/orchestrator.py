from typing import Annotated, Dict, List, Literal, TypedDict
import os
import datetime 

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import display, Image

from agents.project_manager import prompt as project_manager_prompt, tools as project_manager_tools
from agents.scheduler_agent import prompt as scheduler_prompt, tools as scheduler_tools

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from anthropic._exceptions import OverloadedError
import json
from langgraph.graph import MessagesState
from langgraph_supervisor import create_supervisor

# Build out Main States 

llm = ChatAnthropic(model="claude-3-5-haiku-latest")

project_manager_agent = create_react_agent(
    model=llm,
    tools=project_manager_tools,
    prompt=project_manager_prompt,
    name="Project Manager Agent",
)

scheduler_agent = create_react_agent(
    model=llm,
    tools=scheduler_tools,
    prompt=scheduler_prompt,
    name="Scheduler Agent",
)

prompt = (
    "You are a supervisor agent that coordinates the project manager agent and the scheduler agent. "
    "You will receive messages from both agents and you need to decide which agent should take the next action. "
    "For anything related to assignments, tasks, exams, or projects, use project_manager_agent. "
    "For anything related to scheduling, deadlines, or calendar events, use scheduler_agent. "
)

orchestrator_agent = create_supervisor(
    [scheduler_agent, project_manager_agent],
    model=llm,
    output_mode="last_message",
    prompt=prompt,
)


create_orchestrator_graph = orchestrator_agent.compile()
app = create_orchestrator_graph

