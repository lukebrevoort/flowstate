# Import relevant functionality
from langchain.agents import tool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.prompts import PromptTemplate
from notion_client import Client
import os, sys

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from notion_api import NotionAPI, Assignment
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Union
from difflib import get_close_matches
from langchain_anthropic import ChatAnthropic
from dateparser import parse
import re
from langchain_core.runnables import RunnableConfig
from .configuration import Configuration

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

llm = ChatAnthropic(model="claude-3-5-sonnet-latest")

"""
Lets create a project manager that will seperate specific Notion pulled assignments
into manageable subtasks for completion. The project manager will be able to:
1. Retrive assignments from a given Notion database
2. Create substasks for each assignment
3. Create a Todo item/assignment for each substask
4. update assignment submission status and progress
5. Estimate total time of completion for each assignment
6. (For the future) generate a schedule/study plan for each project
"""


def get_user_id_from_config(config: Optional[RunnableConfig] = None) -> str:
    """Get user_id from config or Supabase, with fallback to default"""
    if config and "configurable" in config:
        user_id = config["configurable"].get("user_id")
        if user_id:
            # TODO: Add Supabase lookup logic here if needed
            # For now, return the user_id from config
            return user_id

    # Default user ID when none provided
    return "99d11141-76eb-460f-8741-f2f5e767ba0f"


# Define the tools


@tool
def get_current_time(config: RunnableConfig):
    """
    Get the current date and time.

    Returns the current date and time in a formatted string.
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    current_time = datetime.now()
    time = notion_api.parse_date(current_time)
    return time


@tool
def parse_relative_datetime(date_description: str):
    """
    Convert relative dates with times (tomorrow at 5pm, next Monday at 3pm, etc.)
    into actual datetimes with the correct time component.

    Args:
        date_description: Description of the date and time (e.g., "tomorrow at 5pm")

    Returns:
        ISO format datetime string with the correct date and time
    """

    current_time = datetime.now()

    # Try to extract time information
    time_pattern = r"at\s+(\d+)(?::(\d+))?\s*(am|pm|AM|PM)"
    time_match = re.search(time_pattern, date_description)

    # First parse the date
    parsed_date = parse(date_description, settings={"RELATIVE_BASE": current_time})

    # If we found specific time information, apply it
    if time_match and parsed_date:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        am_pm = time_match.group(3).lower()

        # Convert to 24-hour format
        if am_pm == "pm" and hour < 12:
            hour += 12
        elif am_pm == "am" and hour == 12:
            hour = 0

        # Set the time component
        parsed_date = parsed_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if parsed_date:
        return parsed_date.isoformat()
    return None


@tool
def retrieve_assignment(assignment_name: str, config: RunnableConfig):
    """
    Retrieve a specific assignment by name from Notion.
    Args:
        assignment_name: Name of the assignment to retrieve
        config: RunnableConfig containing user-specific configuration

    Returns:
        Notion page dict if found, else None
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    return notion_api.find_assignment_page(assignment_name)


@tool
def retrieve_assignments(config: RunnableConfig, filters: Dict[str, Any] = None):
    """
    Retrieve a list of assignments from Notion.
    Args:
        config: RunnableConfig containing user-specific configuration
        filters: Optional filters to apply when retrieving assignments

    Returns:
        List of Notion page dicts if found, else empty list
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    return notion_api.find_assignment_pages(filters=filters)
    pass


@tool
def create_assignment(assignment: Assignment, config: RunnableConfig) -> Optional[Dict[str, Any]]:
    """
    Create a new assignment item in Notion based on the provided Assignment dataclass.

    Args:
        assignment: Assignment dataclass instance containing assignment details
        config: RunnableConfig containing user-specific configuration
    Returns:
        Notion page dict if created successfully, else None
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    return notion_api.create_assignment_page(assignment)


@tool
def get_course_info(course_name: str = None, config: RunnableConfig = None) -> Optional[Dict[str, Any]]:
    """
    Retreives course information from Notion based on course name.

    Args:
        course_name: Name of the course to retrieve information for
        config: RunnableConfig containing user-specific configuration

    Returns:
        Course information dict if found, else None
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    return notion_api.get_course_page(course_name)


@tool
def get_all_courses(config: RunnableConfig = None) -> Optional[Dict[str, Any]]:
    """
    Retreives all course information from Notion.

    Args:
        config: RunnableConfig containing user-specific configuration

    Returns:
        List of course information dicts if found, else empty list
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    return notion_api.get_all_course_pages()


@tool
def update_assignment(assignment: Assignment, config: RunnableConfig) -> Dict[str, Any]:
    """
    Update an existing assignment in Notion.

    Args:
        assignment: Assignment dataclass instance containing updated assignment details
        config: RunnableConfig containing user-specific configuration

    Returns:
        Updated Notion page dict if successful, else None
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    return notion_api.update_assignment_page(assignment)


@tool
def update_bulk_pages(updates: Dict[Assignment, Any], config: RunnableConfig) -> Dict[str, Any]:
    """
    Update multiple Notion pages in bulk.

    Args:
        updates: Dictionary mapping assignment names to Assignment datacclass instances with updated details
        config: RunnableConfig containing user-specific configuration

    Returns:
        Dictionary containing the results of the update operations
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    return notion_api.update_assignment_page(updates)


time_prompt = PromptTemplate.from_template(
    """
Given an {assignment}, give an Estimated Time of Completion. This should consider the following factors:
- Due date: {due_date}
- Description: {description}
- Current progress: {status}
- Assignment Notes: {notes}

The time should be in hours and minutes, and should be a rough estimate.
The output should be a simple string with the time in the format "X hours Y minutes" with some explaination as to why.
For example:
"Based on the current progress and the due date, I estimate that it will take approximately 3 hours and 30 minutes to complete this assignment.
This includes time for research, writing, and editing. Would you like me to create subtasks for this assignment?"
"""
)


@tool
def estimate_completion_time(assignment: Assignment = None, config: RunnableConfig = None):
    """
    Estimate the time required to complete an assignment based on its details.
    """
    pass


subtask_prompt = PromptTemplate.from_template(
    """
Break down {assignment} into subtasks considering:
- Current date: {current_date}
- Due date: {due_date}
- Current progress: {status}
- Description: {description}
- Assignment Notes: {notes}

Create NO MORE THAN 5 subtasks that are manageable and specific.
The Due Dates for the each subtask should be set to some time BEFORE the due date of the assignment, but AFTER the current time.
Return ONLY a simple list of subtask names, one per line, with no additional formatting.

Common subtasks for assignments include:
- For essays: Research topic, Create outline, Write first draft, Edit draft, Finalize citations
- For exams: Review lecture notes, Create study guide, Take practice exams, Review weak areas
- For projects: Research topic, Create project plan, Gather materials, Implementation, Final review
"""
)


@tool
def create_subtask_assignment(assignment_dict, config: RunnableConfig):
    """
    Create a subtask assignment in Notion.
    """
    pass


@tool
def create_subtasks(assignment_dict, config: RunnableConfig):
    """
    Create subtasks for a given assignment in Notion.
    """
    pass


@tool
def smart_schedule(config: RunnableConfig):
    """
    Created a smart schedule for the user based on their assignments and deadlines.
    This will analyze all assignments, their due dates, and estimated completion times to create a study/work schedule.
    Information will be passed to scheduler agent for further processing.
    """
    # TO DO
    pass


tools = [
    retrieve_assignment,
    retrieve_assignments,
    get_current_time,
    create_assignment,
    get_course_info,
    parse_relative_datetime,
    update_assignment,
    create_subtasks,
    estimate_completion_time,
    smart_schedule,
]

project_manager_prompt = """

# Project Management Agent for Notion - Tool Usage Guide

## Primary Role
You are an agent specialized in managing academic assignments in Notion using OAuth-authenticated user tokens. You help users track, organize, and complete their academic work efficiently through precise tool usage.

## CRITICAL TOOL USAGE ETIQUETTE

### 1. ALWAYS Use Config Parameter
- EVERY tool call MUST include the `config` parameter containing user authentication
- The config contains user_id for OAuth token retrieval
- Never attempt operations without proper user authentication

### 2. Tool Selection Rules

#### For Information Retrieval - Use These Tools:
- **`get_current_time`** - Get current date/time in user's timezone
- **`retrieve_assignment`** - Find ONE specific assignment by exact name
- **`retrieve_assignments`** - Find MULTIPLE assignments with filters (status, priority, due_date, course_name)
- **`get_course_info`** - Get details about a specific course by name
- **`get_all_courses`** - Get all enrolled courses

#### For Data Creation - Use These Tools:
- **`create_assignment`** - Create new assignment (requires Assignment dataclass)
- **`create_subtasks`** - Break down assignment into manageable subtasks
- **`create_subtask_assignment`** - Create individual subtask as assignment

#### For Data Modification - Use These Tools:
- **`update_assignment`** - Update single assignment properties
- **`update_bulk_pages`** - Update multiple assignments simultaneously
- **`parse_relative_datetime`** - Convert "tomorrow at 5pm" to ISO format

#### For Analysis - Use These Tools:
- **`estimate_completion_time`** - Calculate time needed for assignment completion
- **`smart_schedule`** - Generate study/work schedule based on all assignments

### 3. MANDATORY Tool Usage Patterns

#### For "Show my assignments" requests:
```
ALWAYS use: retrieve_assignments() with appropriate filters
NEVER use: retrieve_assignment() for multiple items
```

#### For "Create new assignment" requests:
```
1. FIRST: get_course_info() if course mentioned
2. THEN: create_assignment() with Assignment dataclass
3. VERIFY: retrieve_assignment() to confirm creation
```

#### For "Update assignment status" requests:
```
1. FIRST: retrieve_assignment() to get current data
2. THEN: update_assignment() with modified Assignment object
3. VERIFY: retrieve_assignment() to confirm changes
```

#### For date/time parsing requests:
```
ALWAYS use: parse_relative_datetime() for natural language dates
Examples: "tomorrow at 5pm", "next Monday at 3pm", "in 2 days at noon"
```

### 4. Data Format Requirements

#### Assignment Dataclass MUST Include:
- **name**: str (REQUIRED - assignment title)
- **course_name**: str (REQUIRED - for course relation)
- **status**: str (Not started, In progress, Completed, Submitted)
- **priority**: str (Low, Medium, High, Urgent)
- **due_date**: datetime (ISO format YYYY-MM-DDTHH:MM:SSZ)
- **description**: str (HTML will be cleaned automatically)


#### Filter Dictionary Format:
```python
# For single-value filters:
filters = {
    "name": "partial_assignment_name",  # Contains search
    "status": "In progress",           # Exact match
    "priority": "High",               # Exact match
    "due_date": "2025-09-27",        # On or after date
    "course_name": "Physics 101"      # Course relation
}

# For multi-value filters (e.g., status IN ["Not started", "In progress"]):
filters = {
    "or": [
        {"property": "Status", "status": {"equals": "Not started"}},
        {"property": "Status", "status": {"equals": "In progress"}}
    ]
}
```

**IMPORTANT:**
- Never pass a list to a property filter (e.g., `"status": ["Not started", "In progress"]` is invalid and will cause a Notion API error).
- To filter for multiple values, always use an `or` filter with individual single-value conditions for each value.

**Example for combining with other filters:**
```python
filters = {
    "and": [
        {
            "or": [
                {"property": "Status", "status": {"equals": "Not started"}},
                {"property": "Status", "status": {"equals": "In progress"}}
            ]
        },
        {"property": "Priority", "select": {"equals": "High"}}
    ]
}
```

### 5. Common Request Mappings

#### "What's due tomorrow?" → 
```python
retrieve_assignments(config, filters={"due_date": "2025-09-27"})
```

### What assignments do I have coming up? →
```python
get_current_time(config)
current_time = parse_relative_datetime("now")
retrieve_assignments(config, filters={"due_date": f"{current_time} to f"{(datetime.fromisoformat(current_time) + timedelta(days=7)).isoformat()}"})
```

#### "Show my physics assignments" →
```python
retrieve_assignments(config, filters={"course_name": "Physics"})
```

#### "Create essay due Friday" →
```python
1. parse_relative_datetime("Friday")
2. create_assignment(Assignment(name="Essay", due_date=parsed_date), config)
```

#### "Mark homework as completed" →
```python
1. retrieve_assignment("homework", config) 
2. update_assignment(Assignment(name="homework", status="Completed"), config)
```

### 6. Error Recovery Protocol

#### If tool fails:
1. Check if user_id exists in config
2. Verify assignment/course names are exact matches
3. Ensure date formats are ISO compliant
4. Retry with corrected parameters
5. If still failing, ask user for clarification

#### For ambiguous requests:
- Ask for specific assignment names
- Confirm course names with get_all_courses()
- Use fuzzy matching cautiously and confirm with user

### 7. NEVER DO THESE:
- ❌ Call tools without config parameter
- ❌ Use retrieve_assignment() for multiple items
- ❌ Create assignments without course information
- ❌ Update assignments without retrieving current data first
- ❌ Assume assignment names - always verify exact matches
- ❌ Use raw datetime strings - always parse with parse_relative_datetime()

### 8. ALWAYS DO THESE:
- ✅ Include config in every tool call
- ✅ Verify operations completed successfully
- ✅ Use appropriate filters for multi-item retrieval
- ✅ Parse dates through parse_relative_datetime() for natural language
- ✅ Get current course list before creating assignments
- ✅ Confirm assignment names with user if uncertain
- ✅ Provide clear status updates after operations

## Response Format
Always provide:
1. Clear confirmation of actions taken
2. Summary of retrieved data in readable format
3. Next suggested actions if applicable
4. Error explanations with suggested corrections

This tool usage protocol ensures reliable, secure, and efficient interaction with user's Notion workspace through proper OAuth authentication and precise API operations.
"""
