# FlowState

FlowState is an advanced AI agent ecosystem built to assist users in managing their academic, personal, and professional projects. Integrating cutting-edge tools, innovative agent orchestration techniques, and external APIs like Notion and Google Calendar, FlowState facilitates seamless task management, time optimization, and priority handling.

---

## Project Overview

FlowState is designed to simplify and optimize task management by providing users with tailored study plans, schedules, and task breakdowns. The system heavily focuses on integration, scalability, and user personalization:

### Key Functionalities

- Connects with **Notion** for managing assignments and tasks.
- Connects with **Google Calendar** to intelligently manage schedules and events.
- Uses advanced AI agents to break down complex tasks into manageable subtasks.
- Provides interfaces with custom-built React components.

---

## Architecture

FlowState adopts a modular architecture divided into distinct subsystems, each orchestrated for specialized purposes. Below is an overview of the core architecture:

### Core Components

#### 1. **Supervisor Agent**

- The orchestrating agent that delegates tasks to specialized sub-agents.
- Ensures every user interaction concludes with properly formatted data.
- Responsible for routing requests to the appropriate agent.

#### 2. **Agents**

- **Project Manager Agent (PMAgent)**:
  - Handles Notion data.
  - Retrieves assignments, creates subtasks, and manages assignments' statuses and priorities.
  - Supports study plan generation and schedule analysis.
  - Critical Tools: `retrieve_assignments`, `create_assignment`, `estimate_completion_time`.

- **Scheduler Agent**:
  - Integrates with Google Calendar.
  - Handles scheduling, event creation, and availability checks.
  - Key Feature: Identifies conflicts, suggests available time slots.
  - Critical Tools: `get_events`, `create_event`, `delete_event`, `find_available_time_slots`.

- **Response Agent**:
  - Formats responses in JSX for the front-end.
  - Always concludes customer-facing interactions.

### Integration Layers

- **Langchain Framework**: Orchestrates task calls, manages data flows, and facilitates conversational logic between agents.
- **APIs**:
  - **Google Calendar API**: OAuth-verified access for calendar integration.
  - **Notion API**: Data synchronization for assignment and course management.

---

## Guidelines for OpenCode Agents

To maintain the integrity and extensibility of FlowState, the following guidelines must be adhered to:

### Coding Standards

1. **Tool-Centric Development**:
   - ALWAYS use the appropriate tools for performing operations.
   - Describe intentions and goals using tools, avoiding assumptions.

2. **Authentication-First Approach**:
   - All operations involving Notion or Google Calendar MUST validate user-access tokens via OAuth configuration.

3. **Error Handling**:
   - Provide meaningful logs for troubleshooting.
   - Use fallback mechanisms for tool/API failures.

4. **Conventions**:
   - Ensure all date-time operations use ISO 8601 formatting.
   - Follow Python PEP 8 standards for code readability and modularity.

5. **Integration Patterns**:
   - Project Manager and Scheduler agents interact indirectly; ensure scoped toolsets usage only.
   - Response Agent handles the final user-facing JSX formatting.
6. Avoid Creating Summary Documents or Explanations within Agents; focus on task execution.

### Pull Requests

- Create comprehensive, descriptive PRs.
- Link tasks to specific issues.
- Ensure code passes pre-defined tests before submission.

---

## Roadmap

**Long-term Enhancements:**

- -Improve Frontend integration with dynamic React components. (Creating custom buttons, forms, and UI's for our agent to use in stead of generate)
- Expand agent automation to incorporate natural language understanding.
- Introduce deep learning integrations for task recommendation.

## Current Roadmap

### Priority 1: Restructure Agent Architecture

#### Build explicit graph with nodes for each agent

from langgraph.graph import StateGraph
workflow = StateGraph(MessagesState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("scheduler", scheduler_node)
workflow.add_node("project_manager", pm_node)
workflow.add_node("response", response_node)

#### Add explicit edges for routing

workflow.add_conditional_edges("supervisor", route_to_agent)
workflow.add_edge("scheduler", "response")
workflow.add_edge("project_manager", "response")
workflow.add_edge("response", END)
Why: Current hybrid approach creates confusion. Pick one pattern and commit to it.

---

### Priority 2: Enforce Response Agent Requirement

Add a validator node:
def validate_final_response(state: MessagesState):
"""Ensure response is in JSX format"""
last_message = state["messages"][-1]

    if not has_jsx_format(last_message.content):
        # Force through Response Agent
        return {"messages": [HumanMessage(
            content=f"Format this response in JSX: {last_message.content}"
        )]}

    return state

#### Add to graph

workflow.add_node("validate", validate_final_response)
workflow.add_edge("response", "validate")
workflow.add_conditional_edges("validate",
lambda x: "end" if has_jsx_format(x["messages"][-1].content) else "response"
)
Why: Structural enforcement prevents inconsistent responses.

---

### Priority 3: Standardize Context Passing

Create a context builder utility:

#### backend/agents/utils.py (new file)

def build_agent_context(
runtime: ToolRuntime,
request: str,
include_profile: bool = True,
include_history: bool = False
) -> str:
"""Build consistent context for sub-agents"""

    original_message = next(
        (msg for msg in runtime.state["messages"] if msg.type == "human"),
        None
    )

    context_parts = []

    if original_message:
        context_parts.append(f"User inquiry: {original_message.content}")

    if include_profile:
        profile = runtime.state.get("user_profile", "No profile available")
        context_parts.append(f"User profile: {profile}")

    if include_history:
        history = runtime.state.get("messages", [])[-5:]  # Last 5 messages
        context_parts.append(f"Recent context: {history}")

    context_parts.append(f"Task: {request}")

    return "\n\n".join(context_parts)

#### Use consistently in all sub-agent tools

@tool
async def schedule_task(request: str, runtime: ToolRuntime) -> str:
prompt = build_agent_context(runtime, request, include_profile=True)
result = await scheduler_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
return result["messages"][-1].content
Why: Consistent context = consistent behavior.

---

Priority 4: Unified Model Strategy
Decision Matrix:

| Agent      | Current | Recommended | Rationale                                      |
| ---------- | ------- | ----------- | ---------------------------------------------- |
| Supervisor | Haiku   | Sonnet      | Needs strong reasoning for routing             |
| PMAgent    | Sonnet  | Sonnet      | Complex Notion operations require intelligence |
| Scheduler  | Haiku   | Haiku       | Calendar ops are straightforward               |
| Response   | Haiku   | Haiku       | JSX formatting is template-based               |

---

### Priority 5: Simplify Prompts

Your prompts are excellent but verbose. Create a hierarchy:
System Level (applies to all):
GLOBAL_AGENT_RULES = """

1. ALWAYS use tools immediately when available
2. NEVER describe what you would do - DO IT
3. Return structured data, not conversational responses
   """
   Agent Level (specific instructions):
   PROJECT_MANAGER_SPECIFIC = """
   You manage Notion assignments. Your tools:

- retrieve_assignments: Get assignments (use filters)
- create_assignment: Make new assignments
- update_assignment: Modify existing assignments
  Always include config parameter in tool calls.
  """
  Combine at runtime:
  full_prompt = f"{GLOBAL_AGENT_RULES}\n\n{PROJECT_MANAGER_SPECIFIC}"
  Why: Reduces duplication, easier to maintain consistency.

---

### Priority 6: Add Response Validation

Create a JSX validator:

#### backend/agents/validators.py (new file)

import re
def validate_jsx_response(content: str) -> tuple[bool, str]:
"""Validate JSX format and completeness"""

    # Check for React Fragment
    if not content.startswith("<>") or not content.endswith("</>"):
        return False, "Missing React Fragment wrapper"

    # Check for unclosed tags
    open_tags = re.findall(r'<([A-Z][a-zA-Z]*)', content)
    close_tags = re.findall(r'</([A-Z][a-zA-Z]*)>', content)

    if sorted(open_tags) != sorted(close_tags):
        return False, f"Unclosed tags detected: {set(open_tags) - set(close_tags)}"

    # Check for required components
    if "Typography" not in content:
        return False, "No Typography components found"

    return True, "Valid JSX"

# Use in Response Agent

response_content = result["messages"][-1].content
is_valid, error_msg = validate_jsx_response(response_content)
if not is_valid: # Retry with explicit instructions
pass
Why: Catch formatting errors before they reach frontend.evelop more universal integrations beyond Google and Notion APIs.

# Roadmap Summary

- Work through creating the priority tasks above.
- Ensure this system is efficent and maintainable through these steps

---

This document is a living reference for the FlowState project; all contributions must maintain the philosophy expressed here to ensure the system remains robust and user-focused.
