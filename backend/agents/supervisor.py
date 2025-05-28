import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from trustcall import create_extractor

from typing import Literal, Optional, TypedDict

from typing import Annotated, Dict, List, Literal, TypedDict, Optional, Any
import os
import datetime 

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt import ToolNode, tools_condition

from agents.project_manager import tools as project_management_tools, project_manager_prompt
from agents.scheduler import tools as scheduler_tools, scheduler_prompt

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
    def invoke(self, messages, **kwargs):
        validated_messages = validate_messages(messages)
        return super().invoke(validated_messages, **kwargs)
    
    async def ainvoke(self, messages, config=None, **kwargs):
        validated_messages = validate_messages(messages)
        return await super().ainvoke(validated_messages, config, **kwargs)


# Initialize the model
model = ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0)

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
You are a supervisor agent that coordinates the project manager agent and the scheduler agent.
You will receive messages from both agents and you need to decide which agent should take the next action.
For anything related to assignments, tasks, exams, or projects, use project_manager_agent by calling the handoff tool.
For anything related to scheduling, deadlines, or calendar events, use scheduler_agent by calling the handoff tool.

You have a long term memory which keeps track of the user's profile (general information about them).

Here is the current User Profile (may be empty if no information has been collected yet):
<user_profile>
{user_profile}
</user_profile>

1. Reason carefully about the user's profile and the task description.
2. Create a plan of which agents to call and what information to pass to them.
3. Decide which agent should take the next action.

CRITICAL INSTRUCTIONS:
- When receiving information back from agents, you MUST ALWAYS provide a helpful response.
- ALWAYS acknowledge information provided by other agents with specific details.
- After an agent returns control to you, summarize what happened and ask the user if they need additional assistance.
- NEVER return an empty response under any circumstances.
- If you see that the user has received information from another agent, ALWAYS acknowledge this explicitly.
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

scheduler_agent = create_react_agent(
    model=model,
    tools=scheduler_tools,
    prompt=scheduler_prompt + "\nTask Description: {task_description}",
    name="Scheduler Agent",
)

project_management_agent = create_react_agent(
    model=model,
    tools=project_management_tools,
    prompt=project_manager_prompt + "\nTask Description: {task_description}",
    name="Project Management Agent",
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
    agent_name="Project Management Agent", 
    name="Project-Management-Handoff-Tool",
    description="Handoff to the Project Management Agent for assignment and task related actions"
)


# Modify the orchestrator_agent definition
orchestrator_agent = create_supervisor(
    [scheduler_agent, project_management_agent],
    model=ValidatedChatAnthropic(model="claude-3-5-haiku-latest", temperature=0),
    add_handoff_back_messages=True,
    tools=[
        scheduler_handoff,
        project_manager_handoff,
    ],
    output_mode="full_history",
    supervisor_name="Orchestrator Supervisor",
    prompt=MODEL_SYSTEM_MESSAGE,
)

# Need to figure out why the ai is repsonding with null after running,
#Also need to fix these handoff tools to not run two seperate runs but instead
# a single run with the handoff tool


# Create the graph + all nodes
builder = StateGraph(MessagesState, config_schema=configuration.Configuration)

def should_continue(state):
    last_msg = state["messages"][-1]
    
    # Terminate on empty non-final messages
    if isinstance(last_msg, AIMessage) and not last_msg.content:
        if len(state["messages"]) > 1:
            return END
            
    if last_msg.tool_calls:
        return "tools"
    return "__end__"

class ValidationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def final_validation(state: ValidationState):
    """Last-chance message validation"""
    return {"messages": validate_messages(state["messages"])}

builder.add_node("validation", final_validation)
builder.add_edge("tools", "validation")
builder.add_edge("validation", "chatbot")

# Add to your existing builder setup
builder.add_conditional_edges(
    "chatbot",
    should_continue,
    {
        "tools": "tools",
        "__end__": END
    }
)

# Define the flow of the memory extraction process
app = orchestrator_agent.compile(name="Orchestrator Supervisor")