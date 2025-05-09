from typing import Annotated, Dict, List, Literal, TypedDict, Optional, Any
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

class ToolCallSpy:
    """
    Class to track tool calls made by the Claude API.
    Similar to the Spy class in the provided code.
    """
    def __init__(self):
        self.called_tools = []
        self.responses = []
        self.timestamp = datetime.datetime.now().isoformat()
    
    def record_tool_call(self, tool_calls: List[Dict[str, Any]]):
        """Record a tool call made by the model"""
        self.called_tools.append(tool_calls)
        
    def record_response(self, response: Any):
        """Record a response from a tool"""
        self.responses.append(response)
        
    def get_tool_stats(self) -> Dict[str, int]:
        """Get statistics about tool usage"""
        stats = {}
        for call_group in self.called_tools:
            for call in call_group:
                if 'name' in call:
                    name = call['name']
                    stats[name] = stats.get(name, 0) + 1
        return stats
    
    def summary(self) -> str:
        """Get a summary of tool usage"""
        stats = self.get_tool_stats()
        if not stats:
            return "No tools were called."
        
        result = ["Tool usage summary:"]
        for name, count in stats.items():
            result.append(f"- {name}: called {count} time(s)")
        
        return "\n".join(result)

class ValidatedChatAnthropic(ChatAnthropic):
    model_config ={"extra": "allow"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spy = ToolCallSpy()
        
    def _validate_tool_messages(self, messages):
        """
        Helper method to clean message history for Claude API.
        
        Claude requires that each tool_use must have a corresponding tool_result
        in the next message. This method ensures this requirement is met.
        """
        if not messages or not isinstance(messages, list):
            return messages
        
        # First, identify all tool use/result pairs
        valid_pairs = []
        regular_messages = []
        
        i = 0
        while i < len(messages) - 1:  # Stop one before the end to check pairs
            msg = messages[i]
            next_msg = messages[i + 1]
            
            # Check if this is a tool use message
            is_tool_use = (hasattr(msg, "additional_kwargs") and 
                        msg.additional_kwargs.get("tool_calls"))
            
            # Check if next message is a tool result that matches
            is_next_tool_result = False
            matching_ids = set()
            
            if is_tool_use and hasattr(next_msg, "tool_call_id"):
                # For single tool result response
                if next_msg.tool_call_id in [
                    tc.get("id") for tc in msg.additional_kwargs.get("tool_calls", [])
                    if tc.get("id")
                ]:
                    is_next_tool_result = True
                    matching_ids.add(next_msg.tool_call_id)
                    
            # Process messages based on their type
            if is_tool_use and is_next_tool_result:
                # This is a valid tool use + result pair
                valid_pairs.append((msg, next_msg))
                i += 2  # Skip both messages in the next iteration
            else:
                # This is a regular message (not part of a valid tool pair)
                if not (hasattr(msg, "tool_call_id") and msg.tool_call_id):
                    # Only include messages that aren't orphaned tool results
                    regular_messages.append(msg)
                i += 1
        
        # Don't forget to check the last message if we haven't processed it yet
        if i == len(messages) - 1:
            last_msg = messages[i]
            if not (hasattr(last_msg, "tool_call_id") and last_msg.tool_call_id):
                regular_messages.append(last_msg)
        
        # Reconstruct the message sequence: regular messages first, then tool pairs
        result = regular_messages[:]
        
        for tool_use, tool_result in valid_pairs:
            result.append(tool_use)
            result.append(tool_result)
        
        # Sort the resulting messages to maintain original conversation flow
        # Map each message to its original position
        message_positions = {id(msg): i for i, msg in enumerate(messages)}
        result.sort(key=lambda msg: message_positions.get(id(msg), float('inf')))
        
        return result
    
    def _extract_tool_info(self, tool_calls, schema_name=None):
        """
        Extract information from tool calls for both patches and new memories.
        
        Args:
            tool_calls: List of tool calls from the model
            schema_name: Optional name of the schema tool to focus on
        """
        if not tool_calls:
            return "No tool calls made."
            
        # Initialize list of changes
        changes = []
        
        for call in tool_calls:
            if 'name' not in call:
                continue
                
            if call['name'] == 'PatchDoc' and 'args' in call:
                # Check if there are any patches
                if call['args'].get('patches'):
                    changes.append({
                        'type': 'update',
                        'doc_id': call['args'].get('json_doc_id'),
                        'planned_edits': call['args'].get('planned_edits'),
                        'value': call['args']['patches'][0].get('value')
                    })
                else:
                    # Handle case where no changes were needed
                    changes.append({
                        'type': 'no_update',
                        'doc_id': call['args'].get('json_doc_id'),
                        'planned_edits': call['args'].get('planned_edits')
                    })
            elif schema_name and call['name'] == schema_name and 'args' in call:
                changes.append({
                    'type': 'new',
                    'name': schema_name,
                    'value': call['args']
                })
            elif not schema_name and 'args' in call:
                changes.append({
                    'type': 'tool_usage',
                    'name': call['name'],
                    'args': call['args']
                })

        # Format results as a single string
        result_parts = []
        for change in changes:
            if change['type'] == 'update':
                result_parts.append(
                    f"Document {change['doc_id']} updated:\n"
                    f"Plan: {change['planned_edits']}\n"
                    f"Added content: {change['value']}"
                )
            elif change['type'] == 'no_update':
                result_parts.append(
                    f"Document {change['doc_id']} unchanged:\n"
                    f"{change['planned_edits']}"
                )
            elif change['type'] == 'new':
                result_parts.append(
                    f"New {change['name']} created:\n"
                    f"Content: {change['value']}"
                )
            else:
                result_parts.append(
                    f"Tool '{change['name']}' called with args: {change['args']}"
                )
        
        return "\n\n".join(result_parts)
    
    def _track_tool_usage(self, messages):
        """
        Track tool usage in the message history.
        
        Returns a dictionary containing the tools used and their call counts.
        """
        tool_usage = {}
        
        for msg in messages:
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("tool_calls"):
                for tool_call in msg.additional_kwargs.get("tool_calls", []):
                    if "name" in tool_call:
                        tool_name = tool_call["name"]
                        tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        return tool_usage
    
    def invoke(self, input, *args, **kwargs):
        if isinstance(input, list):
            valid_messages = self._validate_tool_messages(input)
            # Track tool usage for debugging/analytics
            tool_usage = self._track_tool_usage(valid_messages)
            
            # Record tool calls in the messages for analysis
            for msg in valid_messages:
                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("tool_calls"):
                    self.spy.record_tool_call(msg.additional_kwargs.get("tool_calls"))
            
            result = super().invoke(valid_messages, *args, **kwargs)
            
            # Record result and potentially extract tool info
            if hasattr(result, "additional_kwargs") and result.additional_kwargs.get("tool_calls"):
                self.spy.record_tool_call(result.additional_kwargs.get("tool_calls"))
            
            # Enhanced logging could be added here
            # print(f"Tool call spy summary: {self.spy.summary()}")
            
            return result
        return super().invoke(input, *args, **kwargs)
        
    async def ainvoke(self, input, *args, **kwargs):
        if isinstance(input, list):
            valid_messages = self._validate_tool_messages(input)
            # Track tool usage for debugging/analytics
            tool_usage = self._track_tool_usage(valid_messages)
            
            # Record tool calls in the messages for analysis
            for msg in valid_messages:
                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("tool_calls"):
                    self.spy.record_tool_call(msg.additional_kwargs.get("tool_calls"))
            
            result = await super().ainvoke(valid_messages, *args, **kwargs)
            
            # Record result and potentially extract tool info
            if hasattr(result, "additional_kwargs") and result.additional_kwargs.get("tool_calls"):
                self.spy.record_tool_call(result.additional_kwargs.get("tool_calls"))
            
            # Enhanced logging could be added here
            # print(f"Tool call spy summary: {self.spy.summary()}")
            
            return result
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
