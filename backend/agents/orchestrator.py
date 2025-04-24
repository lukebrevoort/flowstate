from typing import Annotated, Dict, List, Literal, TypedDict
import os
import datetime 

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import display, Image

from agents.project_manager import project_manager_read_prompt, project_manager_cud_prompt, project_cud_tools, project_read_tools
from agents.scheduler_agent import scheduler_cud_prompt, scheduler_read_prompt, scheduler_cud_tools, scheduler_read_tools

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from anthropic._exceptions import OverloadedError
import json
from langgraph.graph import MessagesState
from langgraph_supervisor import create_supervisor

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

class ValidatedChatAnthropic(ChatAnthropic):
    def invoke(self, messages, **kwargs):
        valid_messages = [msg for msg in messages if hasattr(msg, "content") and msg.content]
        return super().invoke(valid_messages, **kwargs)
        
    async def ainvoke(self, *args, **kwargs):
        # Extract messages from args (assuming it's the first arg after self)
        if len(args) > 0:
            messages = args[0]
            valid_messages = [msg for msg in messages if hasattr(msg, "content") and msg.content]
            # Replace the messages in args
            args_list = list(args)
            args_list[0] = valid_messages
            return await super().ainvoke(*args_list, **kwargs)
        return await super().ainvoke(*args, **kwargs)

# Build out Main States 

llm = ValidatedChatAnthropic(model="claude-3-5-haiku-latest")

project_manager_cuda = create_react_agent(
    model=llm,
    tools=project_cud_tools,
    prompt=project_manager_cud_prompt,
    name="Project Manager CUDA Agent",
)

project_manager_rag = create_react_agent(
    model=llm,
    tools=project_read_tools,
    prompt=project_manager_read_prompt,
    name="Project Manager RAG Agent",
)

project_manager_prompt = ("You are the supervisor agent for the project manager agent."
"You will receive messages from the higher Orchestrator agent and you need to decide which agent should take the next action."
"For anything related to creating, updating, or deleting assignments, use project_manager_cuda."
"For anything related to retrieving assignments, finding assignments, or getting course information, use project_manager_rag."
"For anything related to estimating task durations or retrieving notes, use project_manager_rag."
"You MUST ALWAYS respond with a final answer, DO NOT respond with empty text"

)

project_management_team = create_supervisor(
    [project_manager_cuda, project_manager_rag],
    model=llm,
    prompt=project_manager_prompt,
    supervisor_name="Project Manager Supervisor",
    output_mode="full_history",
).compile(name="project_management_team")

scheduler_cuda = create_react_agent(
    model=llm,
    tools=scheduler_cud_tools,
    prompt=scheduler_cud_prompt,
    name="Scheduler CUDA Agent",
)

scheduler_rag = create_react_agent(
    model=llm,
    tools=scheduler_read_tools,
    prompt=scheduler_read_prompt,
    name="Scheduler RAG Agent",
)

scheduler_prompt = ("You are the supervisor agent for the scheduler agent."
"You will receive messages from the higher Orchestrator agent and you need to decide which agent should take the next action."
"For anything related to creating, updating, or deleting calendar events, use scheduler_cuda."
"For anything related to retrieving calendar events, finding calendar events, or getting calendar information, use scheduler_rag."
"You MUST ALWAYS respond with a final answer, DO NOT respond with empty text"
)

scheduler_team = create_supervisor(
    [scheduler_cuda, scheduler_rag],
    model=llm,
    prompt=scheduler_prompt,
    supervisor_name="Scheduler Supervisor",
    output_mode="full_history",
).compile(name="scheduler_team")

prompt = (
    "You are a supervisor agent that coordinates the project manager agent and the scheduler agent. "
    "You will receive messages from both agents and you need to decide which agent should take the next action. "
    "For anything related to assignments, tasks, exams, or projects, use project_manager_agent. "
    "For anything related to scheduling, deadlines, or calendar events, use scheduler_agent. "
)

orchestrator_agent = create_supervisor(
    [scheduler_team, project_management_team],
    model=llm,
    output_mode="full_history",
    supervisor_name="Orchestrator Supervisor",
    prompt=prompt,
).compile(name="Orchestrator Supervisor")


app = orchestrator_agent

