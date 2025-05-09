from typing import Annotated, Dict, List, Literal, TypedDict
import os
import datetime 

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt import ToolNode, tools_condition

from agents.project_manager import project_manager_read_prompt, project_manager_cud_prompt, project_cud_tools, project_read_tools
from agents.scheduler_agent import scheduler_cud_prompt, scheduler_read_prompt, scheduler_cud_tools, scheduler_read_tools

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from anthropic._exceptions import OverloadedError
import json
from langgraph_supervisor import create_supervisor

from langchain_core.tools import tool, BaseTool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import InjectedState

class ValidatedChatAnthropic(ChatAnthropic):
    def _validate_tool_messages(self, messages):
        """
        Helper method to clean message history for Claude API.
        
        Claude requires that each tool_result must have a corresponding tool_use
        in the previous message. This method ensures this requirement is met.
        """
        if not messages or not isinstance(messages, list):
            return messages
        
        # Step 1: Make a first pass to collect all tool_use_ids and tool_result_ids
        tool_use_ids = {}  # Maps tool_use_id -> message index
        tool_result_ids = {}  # Maps tool_result_id -> message index
        
        for i, msg in enumerate(messages):
            # Find tool uses (in AI messages)
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("tool_calls"):
                for tool_call in msg.additional_kwargs.get("tool_calls", []):
                    if "id" in tool_call:
                        tool_use_ids[tool_call["id"]] = i
            
            # Find tool results
            if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                tool_result_ids[msg.tool_call_id] = i
        
        # Step 2: Build new clean message list ensuring proper pairing
        # Only include messages that form valid tool_use -> tool_result pairs
        # or are not part of tool interactions
        valid_messages = []
        
        # Add non-tool messages first
        for i, msg in enumerate(messages):
            is_tool_use = (hasattr(msg, "additional_kwargs") and 
                          msg.additional_kwargs.get("tool_calls"))
            is_tool_result = hasattr(msg, "tool_call_id") and msg.tool_call_id
            
            # Include regular messages (not tool-related)
            if not is_tool_use and not is_tool_result:
                valid_messages.append(msg)
        
        # Add valid tool_use -> tool_result pairs 
        processed_tool_results = set()
        
        for tool_id in tool_use_ids:
            # Only include pairs where both tool_use and tool_result exist
            if tool_id in tool_result_ids:
                tool_use_msg = messages[tool_use_ids[tool_id]]
                tool_result_msg = messages[tool_result_ids[tool_id]]
                
                # Add the tool_use message if not already added
                if tool_use_msg not in valid_messages:
                    valid_messages.append(tool_use_msg)
                
                # Add the corresponding tool_result if not already added
                if tool_result_msg not in valid_messages:
                    valid_messages.append(tool_result_msg)
                    processed_tool_results.add(tool_id)
        
        # Sort the messages to restore the original conversation flow
        # We use the original message indices to sort
        message_indices = {}
        for i, msg in enumerate(valid_messages):
            for j, orig_msg in enumerate(messages):
                if msg == orig_msg:
                    message_indices[i] = j
                    break
        
        valid_messages = [msg for _, msg in sorted(zip(message_indices.values(), valid_messages))]
        
        return valid_messages
    
    def invoke(self, input, *args, **kwargs):
        if isinstance(input, list):
            valid_messages = self._validate_tool_messages(input)
            return super().invoke(valid_messages, *args, **kwargs)
        return super().invoke(input, *args, **kwargs)
        
    async def ainvoke(self, input, *args, **kwargs):
        if isinstance(input, list):
            valid_messages = self._validate_tool_messages(input)
            return await super().ainvoke(valid_messages, *args, **kwargs)
        return await super().ainvoke(input, *args, **kwargs)

# Build out Main States 

llm = ValidatedChatAnthropic(model="claude-3-5-haiku-latest")

# Defining custom handoff tools for supervisor agents

def create_supervisor_handoff_tool(*, agent_name: str, name: str | None, description: str | None) -> BaseTool:

    @tool(name, description=description)
    def handoff_to_agent(
        # you can add additional tool call arguments for the LLM to populate
        # for example, you can ask the LLM to populate a task description for the next agent
        task_description: Annotated[str, "Provide a detailed task description for the next agent, including any relevant context or information needed for this specific agent to complete their tasks."],
        # you can inject the state of the agent that is calling the tool
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        tool_message = ToolMessage(
            content=f"Successfully transferred to {agent_name}",
            name=name,
            tool_call_id=tool_call_id,
        )
        messages = state["messages"]
        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            # NOTE: this is a state update that will be applied to the swarm multi-agent graph (i.e., the PARENT graph)
            update={
                "messages": messages + [tool_message],
                "active_agent": agent_name,
                "task_description": task_description,
            },
        )

    return handoff_to_agent



project_manager_cud = create_react_agent(
    model=llm,
    tools=project_cud_tools,
    prompt=project_manager_cud_prompt + "\n\nTask Description: {task_description}",
    name="Project Manager CUD Agent",
)

project_manager_read = create_react_agent(
    model=llm,
    tools=project_read_tools,
    prompt=project_manager_read_prompt + "\n\nTask Description: {task_description}",
    name="Project Manager READ Agent",
)

project_manager_prompt = ("""
# Supervisor Agent for Notion Project Management

## Primary Role
You are a supervisor agent orchestrating two specialized sub-agents to manage academic assignments in Notion:

1. **CUD Agent** (Create, Update, Delete): Responsible for modifying the Notion database
2. **READ Agent**: Responsible for retrieving and analyzing information from Notion

## Core Responsibilities
- Understand user requests and determine which sub-agent should handle them
- Coordinate the workflow between agents when tasks require multiple operations
- Maintain context and ensure task completion
- Present information back to the user in a clear, helpful format

## Request Handling Guidelines

### For Information Retrieval Tasks (READ Agent):
- Assignments lookup
- Status checking
- Due date inquiries
- Finding relevant course information
- Analyzing workload and scheduling
- Generating reports or summaries

### For Modification Tasks (CUD Agent):
- Creating new assignments and tasks
- Updating assignment properties (status, priority, due dates)
- Creating subtasks for assignments
- Deleting or archiving completed work
- Reorganizing assignments
                          
## Workflow Coordination
For complex requests requiring both retrieval and modification:
1. First delegate to the READ agent to gather necessary information
2. Process and analyze the retrieved data
3. Then delegate to the CUD agent with precise instructions for modifications
4. Verify the changes were made successfully with a final READ operation

## Key Data Formats

When instructing the CUD agent about assignments, ensure proper formatting:
- Assignment dictionary must include 'name' key
- Date formats should follow ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- Required fields for new assignments: name, course_id/course_name
- Optional fields: description, status, due_date, priority

## Common Request Patterns

- "Show my assignments for next week" → READ agent
- "Create a new essay due Friday" → CUD agent
- "Change the priority of my physics homework" → READ agent then CUD agent
- "What's due tomorrow?" → READ agent
- "Add subtasks to my research paper" → READ agent then CUD agent
- "Move all my completed assignments to Done" → READ agent then CUD agent

## Error Handling

- If a sub-agent encounters an error, analyze the cause and retry with adjusted parameters
- If information is ambiguous, ask the user for clarification before proceeding
- For fuzzy matches on assignment names, confirm with the user before making changes
- Verify all operations completed successfully before reporting completion to the user

Always maintain the context of the ongoing task and current state of the user's Notion workspace to provide continuity between operations.
"""

)

project_management_team = create_supervisor(
    [project_manager_cud, project_manager_read],
    model=llm,
    tools=[
        create_supervisor_handoff_tool(
            agent_name="Project Manager CUD Agent",
            name="handoff_to_project_manager_cud",
            description="Handoff to the project manager CUD agent",
        ),
        create_supervisor_handoff_tool(
            agent_name="Project Manager READ Agent",
            name="handoff_to_project_manager_read",
            description="Handoff to the project manager READ agent",
        ),
    ],
    prompt=project_manager_prompt,
    supervisor_name="Project Manager Supervisor",
    output_mode="full_history",
).compile(name="project_management_team")

scheduler_cud = create_react_agent(
    model=llm,
    tools=scheduler_cud_tools,
    prompt=scheduler_cud_prompt + "\n\nTask Description: {task_description}",
    name="Scheduler CUD Agent",
)

scheduler_read = create_react_agent(
    model=llm,
    tools=scheduler_read_tools,
    prompt=scheduler_read_prompt + "\n\nTask Description: {task_description}",
    name="Scheduler READ Agent",
)

scheduler_prompt = ("""
# Supervisor Agent for Google Calendar Management

## Primary Role
You are a supervisor agent orchestrating two specialized sub-agents to manage academic schedules in Google Calendar:

1. **CUD Agent** (Create, Update, Delete): Responsible for modifying Google Calendar events
2. **READ Agent**: Responsible for retrieving and analyzing calendar information

## Core Responsibilities
- Understand user requests and determine which sub-agent should handle them
- Coordinate the workflow between agents when tasks require multiple operations
- Maintain context and ensure task completion
- Present information back to the user in a clear, helpful format

## Request Handling Guidelines

### For Information Retrieval Tasks (READ Agent):
- View schedules for specific time periods
- Find events by name or keywords
- Check availability for specific days/times
- Get calendar mapping information
- Analyze schedule workload and conflicts
- Validate date-day mappings

### For Modification Tasks (CUD Agent):
- Creating new calendar events
- Updating event properties (time, location, description)
- Deleting or canceling events
- Setting up event reminders
- Finding available time slots for new events

## Workflow Coordination

For complex requests requiring both retrieval and modification:
1. First delegate to the READ agent to gather necessary calendar information
2. Process and analyze the retrieved data
3. Then delegate to the CUD agent with precise instructions for modifications
4. Verify the changes were made successfully with a final READ operation

## Critical Date Handling Requirements

- Always validate date-day mappings using the READ agent
- For relative dates (e.g., "tomorrow", "next Wednesday"), get precise dates before operations
- Never assume date calculations without verification
- ALWAYS make sure the YEAR is correct for ANY created events.
- ISO 8601 format required for all date-time values (YYYY-MM-DDTHH:MM:SS)
- Let Google Calendar API handle timezone offsets

## Common Request Patterns

- "What's on my schedule tomorrow?" → READ agent
- "Create a study session for Friday at 3pm" → CUD agent
- "Move my advisor meeting to 2pm" → READ agent then CUD agent 
- "Am I free next Tuesday afternoon?" → READ agent
- "When can I schedule a 2-hour meeting this week?" → READ agent then CUD agent
- "What calendar am I using for work events?" → READ agent

## Error Handling

- If a sub-agent encounters an error, analyze the cause and retry with adjusted parameters
- For event not found errors, confirm with the user before creating new events
- Validate date-day mappings before any calendar operations
- Verify all operations completed successfully before reporting completion to the user

Always maintain context of the ongoing task and current state of the user's calendars to provide continuity between operations. Prevent duplicate events by ensuring proper update vs. create distinction.
"""
)

scheduler_team = create_supervisor(
    [scheduler_cud, scheduler_read],
    model=llm,
    tools=[
        create_supervisor_handoff_tool(
            agent_name="Scheduler CUD Agent",
            name="handoff_to_scheduler_cud",
            description="Handoff to the scheduler CUD agent",
        ),
        create_supervisor_handoff_tool(
            agent_name="Scheduler READ Agent",
            name="handoff_to_scheduler_read",
            description="Handoff to the scheduler READ agent",
        ),
    ],
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

def run_conversation(message):
    """
    Run a conversation with the orchestrator agent.
    
    Args:
        message (str): The user's message
        
    Returns:
        dict: The response from the agent
    """
    # Initial state with the user's message
    initial_state = {
        "messages": [HumanMessage(content=message)],
        "active_agent": None,
        "task_description": None
    }
    
    # Run the orchestrator with the initial state
    result = app.invoke(initial_state)
    
    # Extract the AI's response from the conversation history
    # The last AI message in the history should be the response
    messages = result["messages"]
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return {"response": message.content}
    
    return {"response": "No response generated."}
