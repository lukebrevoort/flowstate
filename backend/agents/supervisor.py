import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from trustcall import create_extractor

from langgraph_supervisor.handoff import create_forward_message_tool
from typing import Literal, Optional, TypedDict

from typing import Annotated, Dict, List, Literal, TypedDict, Optional, Any
import os 

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt import ToolNode, tools_condition

from agents.project_manager import tools as project_management_tools, project_manager_prompt
#from agents.scheduler import tools as scheduler_tools, scheduler_prompt
from agents.response import response_prompt

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from anthropic._exceptions import OverloadedError
import json
from langgraph_supervisor import create_supervisor

from langchain_core.tools import tool, BaseTool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import InjectedState

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import merge_message_runs
from langchain_core.messages import SystemMessage, HumanMessage


from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph_supervisor.handoff import create_forward_message_tool
from langgraph.graph.message import add_messages

import agents.configuration as configuration

## Utilities 

# Inspect the tool calls for Trustcall
class Spy:
    def __init__(self):
        self.called_tools = []

    def __call__(self, run):
        q = [run]
        while q:
            r = q.pop()
            if r.child_runs:
                q.extend(r.child_runs)
            if r.run_type == "chat_model":
                self.called_tools.append(
                    r.outputs["generations"][0][0]["message"]["kwargs"]["tool_calls"]
                )

# Extract information from tool calls for both patches and new memories in Trustcall
def extract_tool_info(tool_calls, schema_name="Memory"):
    """Extract information from tool calls for both patches and new memories.
    
    Args:
        tool_calls: List of tool calls from the model
        schema_name: Name of the schema tool (e.g., "Memory", "ToDo", "Profile")
    """
    # Initialize list of changes
    changes = []
    
    for call_group in tool_calls:
        for call in call_group:
            if call['name'] == 'PatchDoc':
                # Check if there are any patches
                if call['args']['patches']:
                    changes.append({
                        'type': 'update',
                        'doc_id': call['args']['json_doc_id'],
                        'planned_edits': call['args']['planned_edits'],
                        'value': call['args']['patches'][0]['value']
                    })
                else:
                    # Handle case where no changes were needed
                    changes.append({
                        'type': 'no_update',
                        'doc_id': call['args']['json_doc_id'],
                        'planned_edits': call['args']['planned_edits']
                    })
            elif call['name'] == schema_name:
                changes.append({
                    'type': 'new',
                    'value': call['args']
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
        else:
            result_parts.append(
                f"New {schema_name} created:\n"
                f"Content: {change['value']}"
            )
    
    return "\n\n".join(result_parts)

## Schema definitions

# User profile schema
class Profile(BaseModel):
    """This is the profile of the user you are chatting with"""
    name: Optional[str] = Field(description="The user's name", default=None)
    location: Optional[str] = Field(description="The user's location", default=None)
    job: Optional[str] = Field(description="The user's job", default=None)
    connections: list[str] = Field(
        description="Personal connection of the user, such as family members, friends, or coworkers",
        default_factory=list
    )
    interests: list[str] = Field(
        description="Interests that the user has", 
        default_factory=list
    )

## Initialize the model and tools

# Update memory tool
class UpdateMemory(TypedDict):
    """ Decision on what memory type to update """
    update_type: Literal['user', 'todo', 'instructions']

def validate_messages(messages):
    """Ensure all messages have non-empty content except final assistant message"""
    if not messages:
        return messages
        
    cleaned = []
    for i, msg in enumerate(messages):
        if isinstance(msg, AIMessage) and not msg.content:
            if i != len(messages)-1:  # Not final message
                msg.content = "[System: Empty message sanitized]"
        cleaned.append(msg)
    return cleaned

class ValidatedChatAnthropic(ChatAnthropic):
    def invoke(self, input, config=None, **kwargs):
        # Handle both direct messages and input dict
        if isinstance(input, list):
            validated_input = validate_messages(input)
        elif isinstance(input, dict) and "messages" in input:
            validated_input = {**input, "messages": validate_messages(input["messages"])}
        else:
            validated_input = input
            
        return super().invoke(validated_input, config=config, **kwargs)
    
    async def ainvoke(self, input, config=None, **kwargs):
        # Handle both direct messages and input dict
        if isinstance(input, list):
            validated_input = validate_messages(input)
        elif isinstance(input, dict) and "messages" in input:
            validated_input = {**input, "messages": validate_messages(input["messages"])}
        else:
            validated_input = input
            
        return await super().ainvoke(validated_input, config=config, **kwargs)


# Initialize the model
model = ValidatedChatAnthropic(
    model="claude-3-5-haiku-latest", 
    temperature=0,
    streaming=True  # Enable streaming
)

## Create the Trustcall extractors for updating the user profile and ToDo list
profile_extractor = create_extractor(
    model,
    tools=[Profile],
    tool_choice="Profile",
)

## Prompts 


## Tools for handing over the messages to the model
def create_supervisor_handoff_tool(*, agent_name: str, name: str | None, description: str | None) -> BaseTool:

    @tool(name, description=description)
    def handoff_to_agent(
        task_description: Annotated[str, "Provide a detailed task description for the next agent, including any relevant context or information needed for this specific agent to complete their tasks."],
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        # Ensure the content is never empty
        content = f"Successfully transferred to {agent_name}" if agent_name else "Handoff completed"
        
        tool_message = ToolMessage(
            content=content,  # Non-empty content
            name=name,
            tool_call_id=tool_call_id,
        )
        messages = state["messages"]
        
        # Ensure the message has valid content before adding it
        if not tool_message.content:
            tool_message.content = f"Handoff to {agent_name}"
            
        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            update={
                "messages": messages + [tool_message],
                "active_agent": agent_name,
                "task_description": task_description,
            },
        )

    return handoff_to_agent

# Chatbot instruction for choosing what to update and what tools to call 
MODEL_SYSTEM_MESSAGE = """
You are a supervisor agent responsible for orchestrating user interactions through specialized sub-agents. Your role is to coordinate between agents and ensure every user interaction concludes with a properly formatted response.

AVAILABLE AGENTS:
- Project Manager Agent (PMAgent): Handles assignments, tasks, exams, projects, Notion database operations, subtask creation, progress tracking, and time estimation
- Response Agent (ResponseAgent): Generates final JSX-formatted responses for the frontend UI (REQUIRED for all interactions)

AGENT ROUTING RULES:
- For assignments, tasks, exams, projects, Notion operations, subtasks, progress updates, or time estimates → use Project-Management-Handoff-Tool
- After gathering ALL necessary information from sub-agents → ALWAYS use Response-Agent-Handoff-Tool (MANDATORY FINAL STEP)

You have access to long-term memory tracking the user's profile:

<user_profile>
{user_profile}
</user_profile>

MANDATORY WORKFLOW:
1. Analyze the user's request and profile context
2. Route to appropriate specialized agent(s) with detailed task descriptions
3. Collect and process information from sub-agents
4. ALWAYS hand off to Response Agent as the final step - NO EXCEPTIONS
5. The Response Agent will generate the properly formatted JSX response for the frontend

CRITICAL REQUIREMENTS:
- NEVER provide direct responses to users - you are an orchestrator only
- ALWAYS conclude every interaction by routing to the Response Agent
- The Response Agent is the ONLY agent that communicates directly with users
- Pass comprehensive context to the Response Agent including all sub-agent results
- Ensure task descriptions to sub-agents are detailed and include relevant user profile information
- If no specialized processing is needed, still route to Response Agent for proper formatting

HANDOFF PROTOCOL:
- When routing to PMAgent: Include specific details about assignments, deadlines, Notion requirements
- When routing to ResponseAgent: Include all gathered information, user context, and specify the JSX formatting requirements
- Task descriptions should be comprehensive and include relevant user profile details

Remember: You are the conductor of the orchestra - coordinate the agents but let the Response Agent handle all user-facing communication in the proper JSX format for the frontend.
"""

# Trustcall instruction
TRUSTCALL_INSTRUCTION = """Reflect on following interaction. 

Use the provided tools to retain any necessary memories about the user. 

Use parallel tool calling to handle updates and insertions simultaneously.

System Time: {time}"""

# Instructions for updating the ToDo list
CREATE_INSTRUCTIONS = """Reflect on the following interaction.

Based on this interaction, update your instructions for how to update ToDo list items. Use any feedback from the user to update how they like to have items added, etc.

Your current instructions are:

<current_instructions>
{current_instructions}
</current_instructions>"""

## Node definitions


# Currently, only using project management to avoid OAuth issues with Google Calendar
"""
scheduler_agent = create_react_agent(
    model=model,
    tools=scheduler_tools,
    prompt=scheduler_prompt + "\nTask Description: {task_description}",
    name="Scheduler Agent",
)
"""

project_management_agent = create_react_agent(
    model=model,
    tools=project_management_tools,
    prompt=project_manager_prompt + "\nTask Description: {task_description}",
    name="PMAgent",
)

response_agent = create_react_agent(
    model=model,
    tools=[],
    prompt=response_prompt + "\nTask Description: {task_description}\nUser Profile: {user_profile}",
    name="ResponseAgent",
)

# Create supervisor agent (orchestrator)
def get_user_profile(store, config):
    configurable = configuration.Configuration.from_runnable_config(config)
    user_id = configurable.user_id
    todo_category = configurable.todo_category
    namespace = ("profile", todo_category, user_id)
    
    existing_items = store.search(namespace)
    profile_data = {}
    for item in existing_items:
        profile_data.update(item.value)
    
    return Profile(**profile_data).model_dump_json(indent=2)


def update_profile(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and update the memory collection."""
    
    # Get the user ID from the config
    configurable = configuration.Configuration.from_runnable_config(config)
    user_id = configurable.user_id
    todo_category = configurable.todo_category

    # Define the namespace for the memories
    namespace = ("profile", todo_category, user_id)

    # Retrieve the most recent memories for context
    existing_items = store.search(namespace)

    # Format the existing memories for the Trustcall extractor
    tool_name = "Profile"
    existing_memories = ([(existing_item.key, tool_name, existing_item.value)
                          for existing_item in existing_items]
                          if existing_items
                          else None
                        )

    # Merge the chat history and the instruction
    TRUSTCALL_INSTRUCTION_FORMATTED=TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat())
    updated_messages=list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION_FORMATTED)] + state["messages"][:-1]))

    # Invoke the extractor
    result = profile_extractor.invoke({"messages": updated_messages, 
                                         "existing": existing_memories})

    # Save save the memories from Trustcall to the store
    for r, rmeta in zip(result["responses"], result["response_metadata"]):
        store.put(namespace,
                  rmeta.get("json_doc_id", str(uuid.uuid4())),
                  r.model_dump(mode="json"),
            )
    tool_calls = state['messages'][-1].tool_calls
    # Return tool message with update verification
    return {"messages": [{"role": "tool", "content": "updated profile", "tool_call_id":tool_calls[0]['id']}]}

def update_instructions(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and update the memory collection."""
    
    # Get the user ID from the config
    configurable = configuration.Configuration.from_runnable_config(config)
    user_id = configurable.user_id
    todo_category = configurable.todo_category
    
    namespace = ("instructions", todo_category, user_id)

    existing_memory = store.get(namespace, "user_instructions")
        
    # Format the memory in the system prompt
    system_msg = CREATE_INSTRUCTIONS.format(current_instructions=existing_memory.value if existing_memory else None)
    new_memory = model.invoke([SystemMessage(content=system_msg)]+state['messages'][:-1] + [HumanMessage(content="Please update the instructions based on the conversation")])

    # Overwrite the existing memory in the store 
    key = "user_instructions"
    store.put(namespace, key, {"memory": new_memory.content})
    tool_calls = state['messages'][-1].tool_calls
    # Return tool message with update verification
    return {"messages": [{"role": "tool", "content": "updated instructions", "tool_call_id":tool_calls[0]['id']}]}

# Define proper handoff tools for each agent
scheduler_handoff = create_supervisor_handoff_tool(
    agent_name="Scheduler Agent",  
    name="Scheduler-Handoff-Tool",
    description="Handoff to the Scheduler Agent for calendar and scheduling related tasks"
)

project_manager_handoff = create_supervisor_handoff_tool(
    agent_name="PMAgent", 
    name="Project-Management-Handoff-Tool",
    description="Handoff to the Project Management Agent for assignment and task related actions"
)

response_agent_handoff = create_supervisor_handoff_tool(
    agent_name="ResponseAgent", 
    name="Response-Agent-Handoff-Tool",
    description="Handoff to the Response Agent for final responses and user interaction once all information has been gathered"
)



# Modify the orchestrator_agent definition
# Currently, only using project management to avoid OAuth issues with Google Calendar
# scheduler_agent


orchestrator_agent = create_supervisor(
    [project_management_agent, response_agent],
    model=model,
    tools=[
        project_manager_handoff,
        response_agent_handoff,
    ],
    output_mode="full_history",
    supervisor_name="Orchestrator Supervisor",
    prompt=MODEL_SYSTEM_MESSAGE,
)


# Define the function that determines whether to continue or not
def should_continue(state: MessagesState):
    """Determine the next step in the conversation flow"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if last message is an AI message without content (but not the final message)
    if isinstance(last_message, AIMessage) and not last_message.content:
        if len(messages) > 1:
            return "respond"
    
    # If there are tool calls, go to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # If it's an AI message with content, we can respond
    if isinstance(last_message, AIMessage) and last_message.content:
        return "respond"
    
    # Default to respond
    return "respond"

class ValidationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def final_validation(state: ValidationState):
    """Last-chance message validation"""
    return {"messages": validate_messages(state["messages"])}

# Create tools for updating profile and instructions
@tool
def update_user_profile(
    profile_update: Annotated[str, "Instructions for updating the user's profile"],
    state: Annotated[MessagesState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Update the user's profile based on conversation context"""
    return {"messages": [ToolMessage(content="Profile update initiated", tool_call_id=tool_call_id)]}

@tool  
def update_user_instructions(
    instruction_update: Annotated[str, "Instructions for updating user preferences"],
    state: Annotated[MessagesState, InjectedState], 
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Update user instructions based on feedback"""
    return {"messages": [ToolMessage(content="Instructions update initiated", tool_call_id=tool_call_id)]}



# Compile the graph
app = orchestrator_agent.compile(name="Orchestrator Supervisor")

async def stream_response(user_input: str, config: dict):
    """Stream agent steps and tool calls for AgentLoadingCard"""
    
    # Create the initial state
    initial_state = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    final_response = None
    
    # Stream with updates mode and include subgraphs
    async for chunk in app.astream(
        initial_state,
        config=config,
        stream_mode="updates",  # Stream updates instead of messages
        subgraphs=True  # Include subgraph updates
    ):
        # Process updates from different nodes
        for node_name, node_update in chunk.items():
            if node_name == "__start__":
                continue
                
            # Handle supervisor routing decisions
            if "Orchestrator Supervisor" in node_name:
                if hasattr(node_update.get("messages", [{}])[-1], 'tool_calls'):
                    tool_calls = node_update["messages"][-1].tool_calls
                    for tool_call in tool_calls:
                        if "Handoff" in tool_call["name"]:
                            # Extract target agent from tool name
                            if "Project-Management" in tool_call["name"]:
                                target_agent = "Project Management Agent"
                            elif "Response-Agent" in tool_call["name"]:
                                target_agent = "Response Agent"
                            else:
                                target_agent = "Agent"
                            
                            yield {
                                "type": "routing",
                                "agent": "Main Agent",
                                "message": f"Routing request to {target_agent}...",
                                "timestamp": datetime.now().isoformat()
                            }
            
            # Handle sub-agent actions
            elif "PMAgent" in node_name:
                messages = node_update.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    
                    # Check for tool calls
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            yield {
                                "type": "tool",
                                "agent": "Project Management Agent",
                                "message": tool_call["name"],
                                "tool": tool_call["name"],
                                "timestamp": datetime.now().isoformat()
                            }
                    
                    # Check for AI message content indicating actions
                    elif hasattr(last_message, 'content') and last_message.content:
                        # Determine if this is an action or completion based on content
                        content = last_message.content.lower()
                        if any(word in content for word in ["getting", "retrieving", "checking", "analyzing", "processing"]):
                            step_type = "action"
                        else:
                            step_type = "completion"
                        
                        yield {
                            "type": step_type,
                            "agent": "Project Management Agent",
                            "message": last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content,
                            "timestamp": datetime.now().isoformat()
                        }
            
            # Handle Response Agent
            elif "ResponseAgent" in node_name:
                messages = node_update.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content') and last_message.content:
                        # Capture the final response content
                        final_response = last_message.content
                        
                        yield {
                            "type": "completion",
                            "agent": "Response Agent",
                            "message": "Formatting response for display...",
                            "timestamp": datetime.now().isoformat()
                        }
    
    # After all streaming is complete, yield the final response
    if final_response:
        yield {
            "type": "final_response",
            "agent": "Response Agent",
            "message": "Response ready",
            "content": final_response,
            "timestamp": datetime.now().isoformat()
        }

async def stream_events(user_input: str, config: dict):
    """Stream detailed events from the supervisor agent for debugging"""
    
    initial_state = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    async for event in app.astream_events(
        initial_state,
        config=config,
        version="v2"
    ):
        # Handle different event types for more granular control
        if event["event"] == "on_chain_start":
            # Agent starting
            agent_name = event.get("name", "Unknown Agent")
            if agent_name != "RunnableSequence":  # Filter out generic sequences
                yield {
                    "type": "routing",
                    "agent": "Main Agent",
                    "message": f"Starting {agent_name}...",
                    "timestamp": datetime.now().isoformat()
                }
        
        elif event["event"] == "on_tool_start":
            # Tool execution starting
            tool_name = event["name"]
            yield {
                "type": "tool", 
                "agent": event.get("tags", {}).get("agent", "Agent"),
                "message": tool_name,
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }
        
        elif event["event"] == "on_chain_end":
            # Agent completing
            agent_name = event.get("name", "Unknown Agent")
            if agent_name != "RunnableSequence" and "Agent" in agent_name:
                yield {
                    "type": "completion",
                    "agent": agent_name,
                    "message": f"Completed processing with {agent_name}",
                    "timestamp": datetime.now().isoformat()
                }