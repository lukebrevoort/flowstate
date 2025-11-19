"""
StateGraph-based Multi-Agent Supervisor for FlowState
Implements explicit routing with mandatory Response Agent enforcement
"""

import uuid
import re
import json
from datetime import datetime
from typing import Annotated, Dict, List, Literal, Optional, Any, TypedDict

from pydantic import BaseModel, Field

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

import agents.configuration as configuration
from agents.project_manager import tools as project_management_tools, project_manager_prompt
from agents.scheduler import tools as scheduler_tools, scheduler_prompt
from agents.response import response_prompt

# ============================================================================
# ENHANCED STATE SCHEMA
# ============================================================================


class AgentState(TypedDict):
    """Enhanced state that tracks agent routing and context"""

    messages: Annotated[list[BaseMessage], add_messages]
    current_agent: Optional[str]  # Track which agent is processing
    needs_response_formatting: bool  # Flag to ensure Response Agent runs
    user_profile: Optional[str]  # User context for personalization
    agent_results: Dict[str, Any]  # Store results from each agent


# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Using Haiku 4.5 across the board for cost optimization
# Can be upgraded per-agent if needed in the future
base_model = ChatAnthropic(
    model_name="claude-haiku-4-5-20251001",
    temperature=0,
    max_tokens_to_sample=4096,
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def sanitize_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Sanitize messages to prevent Anthropic API errors.
    Strips trailing whitespace from message content.
    """
    sanitized = []
    for msg in messages:
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            # Strip trailing whitespace from content
            cleaned_content = msg.content.rstrip()
            
            # Create new message with cleaned content
            if isinstance(msg, HumanMessage):
                sanitized.append(HumanMessage(content=cleaned_content, id=msg.id if hasattr(msg, 'id') else None))
            elif isinstance(msg, AIMessage):
                sanitized.append(AIMessage(
                    content=cleaned_content,
                    id=msg.id if hasattr(msg, 'id') else None,
                    additional_kwargs=msg.additional_kwargs if hasattr(msg, 'additional_kwargs') else {},
                    response_metadata=msg.response_metadata if hasattr(msg, 'response_metadata') else {}
                ))
            elif isinstance(msg, SystemMessage):
                sanitized.append(SystemMessage(content=cleaned_content, id=msg.id if hasattr(msg, 'id') else None))
            else:
                sanitized.append(msg)
        else:
            sanitized.append(msg)
    
    return sanitized


# ============================================================================
# AGENT NODES
# ============================================================================


async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor node - analyzes user request and routes to appropriate agent
    """
    messages = state["messages"]
    
    # Sanitize messages to prevent trailing whitespace errors
    messages = sanitize_messages(messages)

    # Get user profile for context
    user_profile = state.get("user_profile", "No profile information available")

    # Build routing decision prompt
    supervisor_prompt = f"""You are the FlowState supervisor agent. Your job is to analyze the user's request and decide which specialized agent should handle it.

Available agents:
- "scheduler": Handles Google Calendar operations (viewing events, creating/updating/deleting events, finding availability)
- "project_manager": Handles Notion operations (assignments, tasks, exams, projects, subtasks, progress tracking)
- "general": For general conversation, questions, or when no specialized agent is needed

User Profile:
{user_profile}

Analyze the user's request and respond with ONLY ONE of these exact words: scheduler, project_manager, or general

Do not provide explanation, just the agent name."""

    # Add system message and invoke
    routing_messages = [SystemMessage(content=supervisor_prompt)] + messages

    response = await base_model.ainvoke(routing_messages)

    # Extract routing decision
    content = response.content if hasattr(response, "content") else str(response)
    agent_choice = str(content).strip().lower() if content else "general"

    # Validate choice
    if agent_choice not in ["scheduler", "project_manager", "general"]:
        agent_choice = "general"

    return {"current_agent": agent_choice, "needs_response_formatting": True, "messages": [response]}  # Always need formatting


async def project_manager_node(state: AgentState) -> Dict[str, Any]:
    """
    Project Manager Agent - handles Notion assignment operations
    Loops internally until all tool calls are complete
    """
    messages = state["messages"]
    user_profile = state.get("user_profile", "")
    
    # Sanitize messages to prevent trailing whitespace errors
    messages = sanitize_messages(messages)

    # Build context-aware prompt
    context_prompt = f"""User Profile:
{user_profile}

{project_manager_prompt}"""

    # Create agent with tools
    pm_agent_messages = [SystemMessage(content=context_prompt)] + messages

    # Bind tools to model
    model_with_tools = base_model.bind_tools(project_management_tools)

    # LOOP until agent is done with all tool calls
    max_iterations = 10  # Safety limit
    iteration = 0
    current_messages = pm_agent_messages
    all_new_messages = []
    response = None

    print(f"\n🔄 Project Manager Agent - Starting tool execution loop")

    while iteration < max_iterations:
        iteration += 1
        print(f"  📍 Iteration {iteration}/{max_iterations}")

        # Invoke agent
        response = await model_with_tools.ainvoke(current_messages)
        all_new_messages.append(response)

        # Check if there are tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_names = [tc.get("name", "unknown") for tc in response.tool_calls]
            print(f"  🔧 Tools requested: {', '.join(tool_names)}")

            # Execute tools
            tool_node = ToolNode(project_management_tools)
            tool_results = await tool_node.ainvoke({"messages": [response]})

            # Add tool results to messages
            all_new_messages.extend(tool_results["messages"])

            # Update current messages for next iteration
            current_messages = pm_agent_messages + all_new_messages
        else:
            # No more tool calls, agent is done
            print(f"  ✅ Agent completed task (no more tool calls)")
            break

    print(f"🏁 Project Manager Agent - Completed after {iteration} iterations\n")

    # Get final response content
    final_content = response.content if (response and hasattr(response, "content")) else "Task completed"

    return {"messages": all_new_messages, "agent_results": {"project_manager": final_content}}


async def scheduler_node(state: AgentState) -> Dict[str, Any]:
    """
    Scheduler Agent - handles Google Calendar operations
    Loops internally until all tool calls are complete
    """
    messages = state["messages"]
    user_profile = state.get("user_profile", "")
    
    # Sanitize messages to prevent trailing whitespace errors
    messages = sanitize_messages(messages)

    # Build context-aware prompt
    context_prompt = f"""User Profile:
{user_profile}

{scheduler_prompt}"""

    # Create agent with tools
    scheduler_messages = [SystemMessage(content=context_prompt)] + messages

    # Bind tools to model
    model_with_tools = base_model.bind_tools(scheduler_tools)

    # LOOP until agent is done with all tool calls
    max_iterations = 10  # Safety limit
    iteration = 0
    current_messages = scheduler_messages
    all_new_messages = []
    response = None

    print(f"\n🔄 Scheduler Agent - Starting tool execution loop")

    while iteration < max_iterations:
        iteration += 1
        print(f"  📍 Iteration {iteration}/{max_iterations}")

        # Invoke agent
        response = await model_with_tools.ainvoke(current_messages)
        all_new_messages.append(response)

        # Check if there are tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_names = [tc.get("name", "unknown") for tc in response.tool_calls]
            print(f"  🔧 Tools requested: {', '.join(tool_names)}")

            # Execute tools
            tool_node = ToolNode(scheduler_tools)
            tool_results = await tool_node.ainvoke({"messages": [response]})

            # Add tool results to messages
            all_new_messages.extend(tool_results["messages"])

            # Update current messages for next iteration
            current_messages = scheduler_messages + all_new_messages
        else:
            # No more tool calls, agent is done
            print(f"  ✅ Agent completed task (no more tool calls)")
            break

    print(f"🏁 Scheduler Agent - Completed after {iteration} iterations\n")

    # Get final response content
    final_content = response.content if (response and hasattr(response, "content")) else "Task completed"

    return {"messages": all_new_messages, "agent_results": {"scheduler": final_content}}


async def general_response_node(state: AgentState) -> Dict[str, Any]:
    """
    Handles general queries that don't need specialized agents
    """
    messages = state["messages"]
    user_profile = state.get("user_profile", "")
    
    # Sanitize messages to prevent trailing whitespace errors
    messages = sanitize_messages(messages)

    general_prompt = f"""You are a helpful AI assistant for FlowState, an academic task and schedule management system.

User Profile:
{user_profile}

Provide helpful responses to general questions. Keep responses concise and relevant."""

    response_messages = [SystemMessage(content=general_prompt)] + messages
    response = await base_model.ainvoke(response_messages)

    return {"messages": [response], "agent_results": {"general": response.content}}


async def response_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    MANDATORY Response Agent - formats all responses as JSX for frontend
    This node is ALWAYS executed as the final step
    """
    messages = state["messages"]
    user_profile = state.get("user_profile", "")
    agent_results = state.get("agent_results", {})
    
    # Sanitize messages to prevent trailing whitespace errors
    messages = sanitize_messages(messages)

    # Get the original user query
    original_query = next((msg.content for msg in messages if isinstance(msg, HumanMessage)), "User query")

    # Get the agent's response
    agent_response = ""
    if agent_results:
        # Get the last agent's result
        agent_response = list(agent_results.values())[-1]
    else:
        # Fallback to last AI message
        agent_response = next(
            (msg.content for msg in reversed(messages) if isinstance(msg, AIMessage)), "No response generated"
        )

    # Build comprehensive prompt for Response Agent
    formatting_prompt = f"""{response_prompt}

User Query: {original_query}

User Profile:
{user_profile}

Agent Response to Format:
{agent_response}

Format the above response as valid JSX using Typography, Button, and other available components."""

    # Include user message and system message
    response_messages = [
        SystemMessage(content=formatting_prompt),
        HumanMessage(content="Please format the above response as JSX."),
    ]
    jsx_response = await base_model.ainvoke(response_messages)

    # Validate JSX
    jsx_content = jsx_response.content if hasattr(jsx_response, "content") else str(jsx_response)
    jsx_content_str = str(jsx_content) if jsx_content else ""
    if not _validate_jsx(jsx_content_str):
        # Retry with explicit validation instruction
        retry_prompt = f"""The previous JSX was invalid. Please fix it.

Requirements:
- Must start with <> and end with </>
- All tags must be properly closed
- Use Typography components for text
- Ensure className attributes are complete

Previous attempt:
{jsx_content_str}

Generate corrected JSX:"""

        retry_messages = [SystemMessage(content=response_prompt), HumanMessage(content=retry_prompt)]
        jsx_response = await base_model.ainvoke(retry_messages)

    return {"messages": [jsx_response], "needs_response_formatting": False}  # Mark as complete


# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================


def route_after_supervisor(state: AgentState) -> str:
    """Route to the appropriate agent based on supervisor decision"""
    current_agent = state.get("current_agent", "general")

    if current_agent == "scheduler":
        return "scheduler"
    elif current_agent == "project_manager":
        return "project_manager"
    else:
        return "general"


def should_format_response(state: AgentState) -> str:
    """Always route to response agent for formatting"""
    # This enforces that Response Agent is ALWAYS called
    return "response_agent"


# ============================================================================
# JSX VALIDATION
# ============================================================================


def _validate_jsx(content: str) -> bool:
    """Validate JSX format"""
    if not content:
        return False

    # Check for React Fragment
    if not ("<>" in content and "</>" in content):
        return False

    # Check for basic JSX structure
    if "Typography" not in content:
        return False

    # Check for balanced tags
    open_count = content.count("<")
    close_count = content.count(">")
    if open_count != close_count:
        return False

    # Check for obvious unclosed tags - simple heuristic
    # Count opening and closing Typography tags
    typography_opens = len(re.findall(r"<Typography[^>]*>", content))
    typography_closes = content.count("</Typography>")
    if typography_opens != typography_closes:
        return False

    return True


# ============================================================================
# BUILD THE STATEGRAPH
# ============================================================================


def create_flowstate_graph(checkpointer=None):
    """
    Create the FlowState multi-agent graph with explicit routing

    Args:
        checkpointer: Optional checkpointer for persistent conversation history
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("scheduler", scheduler_node)
    workflow.add_node("project_manager", project_manager_node)
    workflow.add_node("general", general_response_node)
    workflow.add_node("response_agent", response_agent_node)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add conditional routing from supervisor to specialized agents
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"scheduler": "scheduler", "project_manager": "project_manager", "general": "general"},
    )

    # CRITICAL: All agents MUST route to response_agent
    # This enforces consistent JSX formatting
    workflow.add_edge("scheduler", "response_agent")
    workflow.add_edge("project_manager", "response_agent")
    workflow.add_edge("general", "response_agent")

    # Response agent is the final step
    workflow.add_edge("response_agent", END)

    # Compile with checkpointer for conversation persistence
    return workflow.compile(checkpointer=checkpointer)


# Create the compiled graph with checkpointer for conversation persistence
# This enables the agent to remember conversation history within each thread
checkpointer = MemorySaver()
app = create_flowstate_graph(checkpointer=checkpointer)


# ============================================================================
# STREAMING FUNCTIONS (Updated for new graph structure)
# ============================================================================


async def stream_response(user_input: str, config: dict):
    """
    Stream agent steps for the new StateGraph architecture
    """
    print(f"stream_response called with input: {user_input}")

    try:
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "current_agent": None,
            "needs_response_formatting": True,
            "user_profile": None,  # TODO: Load from store
            "agent_results": {},
        }

        # Stream the graph execution
        # Type ignore for config - RunnableConfig compatibility
        async for chunk in app.astream(initial_state, config=config, stream_mode="updates"):  # type: ignore
            try:
                print(f"\n{'='*80}")
                print(f"🔍 CHUNK: {chunk}")
                print(f"{'='*80}\n")

                # Chunk format: {node_name: node_output}
                for node_name, node_output in chunk.items():
                    if node_name == "__start__" or node_name == "__end__":
                        continue

                    print(f"📍 Node: {node_name}")

                    # Yield routing information
                    if node_name == "supervisor":
                        agent_choice = node_output.get("current_agent", "unknown")
                        yield {
                            "type": "routing",
                            "agent": "Supervisor",
                            "message": f"Routing to {agent_choice} agent...",
                            "timestamp": datetime.now().isoformat(),
                        }

                    # Yield agent activity
                    elif node_name in ["scheduler", "project_manager", "general"]:
                        yield {
                            "type": "action",
                            "agent": node_name.replace("_", " ").title(),
                            "message": f"Processing request...",
                            "timestamp": datetime.now().isoformat(),
                        }

                    # Yield final response
                    elif node_name == "response_agent":
                        messages = node_output.get("messages", [])
                        if messages:
                            final_message = messages[-1]
                            jsx_content = final_message.content if hasattr(final_message, "content") else str(final_message)

                            # Strip markdown code fences if present
                            if jsx_content.startswith("```"):
                                lines = jsx_content.split("\n")
                                if lines[0].strip().startswith("```"):
                                    lines = lines[1:]
                                if lines and lines[-1].strip() == "```":
                                    lines = lines[:-1]
                                jsx_content = "\n".join(lines)

                            yield {
                                "type": "completion",
                                "agent": "Response Agent",
                                "message": "Formatting response...",
                                "timestamp": datetime.now().isoformat(),
                            }

                            yield {
                                "type": "final_response",
                                "agent": "Response Agent",
                                "message": "Response ready",
                                "content": jsx_content,
                                "timestamp": datetime.now().isoformat(),
                            }

            except Exception as chunk_error:
                print(f"Error processing chunk: {chunk_error}")
                continue

    except Exception as e:
        print(f"Error in stream_response: {e}")
        import traceback

        traceback.print_exc()
        yield {
            "type": "error",
            "agent": "System",
            "message": f"Streaming error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }


# Placeholder for stream_events - can be implemented similarly if needed
async def stream_events(user_input: str, config: dict):
    """Stream detailed events (placeholder for now)"""
    async for event in stream_response(user_input, config):
        yield event


print("✅ StateGraph-based supervisor loaded successfully")
