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

llm = ChatAnthropic(model="claude-3-5-haiku-latest")

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
    """Get user_id from config, with fallback to default"""
    if config and "configurable" in config:
        return config["configurable"].get("user_id", "default-user")
    return "default-user"


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
    time = notion_api._parse_date(current_time)
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
    Retrieve assignments from a given Notion database

    returns a object with all assignment information included
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    assignment = notion_api.get_assignment_page(assignment_name)
    return assignment


@tool
def retrieve_all_assignments(current_time: str, end_time: str, config: RunnableConfig):
    """
    Retrieve all assignments from the Notion database with date filtering.

    Args:
        current_time: ISO datetime string to filter assignments after this time
        end_time: ISO datetime string to filter assignments before this time

    Returns:
        A list of assignment objects with details including name, due date, status, and course
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    assignments = notion_api.get_all_assignments(current_time, end_time)
    return assignments


@tool
def find_assignment(query: str, config: RunnableConfig):
    """
    Find an assignment using fuzzy matching on the name.

    Args:
        query: Text to search for in assignment names

    Returns:
        The best matching assignment or a list of possible matches
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    assignments = notion_api.get_all_assignments()

    # Extract just the names for matching
    names = [a["name"] for a in assignments]

    # If exact match exists, return it
    if query in names:
        for assignment in assignments:
            if assignment["name"] == query:
                return assignment

    # Try fuzzy matching
    matches = get_close_matches(query, names, n=3, cutoff=0.6)

    if not matches:
        return f"No assignments found matching '{query}'"

    if len(matches) == 1:
        # Return the single match
        for assignment in assignments:
            if assignment["name"] == matches[0]:
                return assignment

    # Return possible matches for clarification
    return {
        "message": f"Multiple assignments found matching '{query}'",
        "matches": matches,
    }


@tool
def create_assignment_item(assignment_dict: Dict[str, Any], config: RunnableConfig):
    """
    Create a assignment in Notion that follows the imported Assignment schema.
    Below is an example of the schema:

    assignment = Assignment(
        name="Midterm Research Paper",
        description="<p>Write a 10-page research paper on a topic of your choice.</p>",
        course_id=77456,  # Maps to a Notion course page via course_mapping
        status="Not started",
        due_date="2025-04-15T23:59:00Z",
        id=67890,
        priority="High",
        group_name="Papers",
        group_weight=30.0,
        grade=None
    )


    returns the created assignment object

    """
    user_id = get_user_id_from_config(config)

    if isinstance(assignment_dict, dict):
        assignment = Assignment(
            name=assignment_dict.get("name"),
            description=assignment_dict.get("description"),
            course_id=assignment_dict.get("course_id"),
            course_name=assignment_dict.get("course_name"),
            status=assignment_dict.get("select", "Not started"),  # Changed from 'select' to 'status' to match expected input
            due_date=assignment_dict.get("due_date"),
            id=assignment_dict.get("id"),
            priority=assignment_dict.get("priority", "Medium"),
            group_name=assignment_dict.get("group_name"),
            group_weight=assignment_dict.get("group_weight"),
            grade=assignment_dict.get("grade"),
        )
    else:
        assignment = assignment_dict

    notion_api = NotionAPI(user_id=user_id)
    print(f"Creating assignment with due date: {assignment.due_date}")
    notion_api.create_assignment(assignment)
    return assignment


@tool
def get_course_info(course_name: str = None, config: RunnableConfig = None):
    """
    Get course information from Notion database.

    Args:
        course_name: (Optional) Name or code of the course to search for

    Returns:
        If course_name is provided and found: Dict with course_id and course_name
        If course_name is provided but not found: Dict with all course names and their IDs
        If course_name is not provided: Dict with all course names and their IDs
    """
    user_id = get_user_id_from_config(config) if config else "default-user"
    notion_api = NotionAPI(user_id=user_id)

    # Get mappings
    course_name_dict = notion_api._get_course_id_name_mapping()
    course_id_dict = notion_api._get_course_id_mapping()

    # Create a comprehensive dict with both names and IDs
    course_info = {}
    for name, notion_id in course_name_dict.items():
        canvas_id = None
        # Find the canvas_id that maps to this notion_id
        for canvas_key, notion_value in course_id_dict.items():
            if notion_value == notion_id:
                canvas_id = canvas_key
                break

        course_info[name] = {"notion_id": notion_id, "course_id": canvas_id}

    # If no course name provided, return all course info
    if not course_name:
        return course_info

    # Try to find the course by exact match
    if course_name in course_info:
        return {course_name: course_info[course_name]}

    # Try to find by case-insensitive partial match
    for name in course_info:
        if course_name.lower() in name.lower():
            return {name: course_info[name]}

    # If not found, return all course info
    return course_info


@tool
def update_assignment(
    name: str,
    priority: str = None,
    status: str = None,
    due_date: str = None,
    description: str = None,
    config: RunnableConfig = None,
) -> str:
    """
    Update an assignment in Notion.

    Args:
        name: Name of the assignment to update (required)
        priority: Priority level (High, Medium, Low)
        status: Status (Not started, In progress, Completed)
        due_date: Due date in ISO format
        description: Description text

    Returns:
        String confirmation of update or error message
    """
    user_id = get_user_id_from_config(config) if config else "default-user"

    # Build the dictionary from the individual parameters
    assignment_dict = {"name": name}
    if priority is not None:
        assignment_dict["priority"] = priority
    if status is not None:
        assignment_dict["select"] = status  # NotionAPI will now use select instead of status internally
    if due_date is not None:
        assignment_dict["due_date"] = due_date
    if description is not None:
        assignment_dict["description"] = description

    # Initialize the NotionAPI
    notion_api = NotionAPI(user_id=user_id)
    try:
        # Attempt to update the assignment
        updated_assignment = notion_api.update_assignment(assignment_dict)
        return f"Assignment updated successfully: {updated_assignment.get('title', 'Unknown')}"
    except Exception as e:
        # Log the error and return a message
        logger.error(f"Error updating assignment: {e}")
        return f"Failed to update assignment: {e}"


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
def estimate_completion_time(assignment_dict):
    """
    Generate an estimated time of completion given an assignment dictionary.

    Args:
        assignment_dict: Dictionary containing assignment details.
        MUST INCLUDE 'name', 'due_date', 'status', and 'description'.

    Returns:
        Estimated time of completion as a string.
    """
    chain = time_prompt | llm

    # Get the current time
    current_time = datetime.now()

    estimated_time = chain.invoke(
        {
            "assignment": assignment_dict["name"],
            "due_date": assignment_dict["due_date"],
            "status": assignment_dict.get("select", "Not started"),
            "description": assignment_dict.get("description", ""),
            "current_time": current_time.isoformat(),
            "notes": get_assignment_notes(assignment_dict["name"]),
        }
    )

    if estimated_time:
        return estimated_time.content
    else:
        logger.error("Failed to estimate completion time.")
        return "Failed to estimate completion time."

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
    Creates assignment subtasks in notion that follow the Assignment Schema

    assignment = Assignment(
        name="Midterm Research Paper",
        description="<p>Write a 10-page research paper on a topic of your choice.</p>",
        course_id=77456,  # Maps to a Notion course page via course_mapping
        status="Not started",
        due_date="2025-04-15T23:59:00Z",
        id=67890,
        priority="High",
        group_name="Papers",
        group_weight=30.0,
        grade=None
    )
    """

    user_id = get_user_id_from_config(config)

    if isinstance(assignment_dict, dict):
        assignment = Assignment(
            name=assignment_dict.get("name"),
            description=assignment_dict.get("description"),
            course_id=assignment_dict.get("course_id"),
            course_name=assignment_dict.get("course_name"),
            status=assignment_dict.get("select", "Not started"),  # Changed from 'select' to 'status' to match expected input
            due_date=assignment_dict.get("due_date"),
            id=assignment_dict.get("id"),
            priority=assignment_dict.get("priority", "Medium"),
            group_name=assignment_dict.get("group_name"),
            group_weight=assignment_dict.get("group_weight"),
            grade=assignment_dict.get("grade"),
        )
    else:
        assignment = assignment_dict

    notion_api = NotionAPI(user_id=user_id)
    print(f"Creating assignment with due date: {assignment.due_date}")
    notion_api.create_assignment(assignment)
    return assignment


@tool
def create_subtasks(assignment_dict, config: RunnableConfig):
    """
    Create subtasks for a given assignment and add them to Notion.

    Args:
        assignment: Dictionary containing assignment details.

    Returns:
        List of subtask dictionaries ready to be created in Notion.
    """
    user_id = get_user_id_from_config(config)
    logger.info(f"Generating subtasks for user {user_id}, assignment: {assignment_dict.get('name', 'Unknown')}")

    try:
        chain = subtask_prompt | llm

        if "current_date" not in assignment_dict:
            current_time = datetime.now().replace(microsecond=0)
            assignment_dict["current_date"] = current_time.isoformat()

        # Get subtasks from LLM
        subtasks_result = chain.invoke(
            {
                "assignment": assignment_dict["name"],
                "current_date": assignment_dict["current_date"],
                "due_date": assignment_dict["due_date"],
                "status": assignment_dict.get("select", "Not started"),
                "description": assignment_dict.get("description", ""),
                "notes": get_assignment_notes(assignment_dict["name"]),
            }
        )

        # Parse the LLM output into a list of subtask names
        subtask_names = subtasks_result.content.strip().split("\n")

        # Calculate time gap for evenly spaced subtasks
        from dateutil import parser
        import random

        # Parse dates properly with consistent timezone handling
        start_date = parser.parse(assignment_dict["current_date"])
        due_date = parser.parse(assignment_dict["due_date"])

        # Ensure both dates have timezone info (use UTC if not specified)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)

        # Make sure start date is before due date
        if start_date > due_date:
            logger.warning(f"Start date {start_date} is after due date {due_date}. Using current time.")
            start_date = datetime.now(timezone.utc)

        # Calculate time span in seconds
        time_span = max((due_date - start_date).total_seconds(), 3600)  # Minimum 1 hour
        time_step = time_span / (len(subtask_names) + 1)

        # Create a list of dictionaries for each subtask
        subtask_dicts = []
        for i, subtask_name in enumerate(subtask_names):
            # Calculate subtask due time
            subtask_due = start_date + timedelta(seconds=(i + 1) * time_step)

            # Round to the nearest half hour
            minute = subtask_due.minute
            if minute < 15:
                subtask_due = subtask_due.replace(minute=0, second=0, microsecond=0)
            elif 15 <= minute < 45:
                subtask_due = subtask_due.replace(minute=30, second=0, microsecond=0)
            else:
                subtask_due = subtask_due.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

            # Format with consistent timezone
            subtask_due_str = subtask_due.isoformat()

            # Create subtask dictionary
            subtask_dict = {
                "name": f"{subtask_name} - {assignment_dict['name']}",
                "description": f"<p>Subtask for: {assignment_dict['name']}</p>",
                "course_id": assignment_dict.get("course_id"),
                "course_name": assignment_dict.get("course_name"),
                "status": "Not started",
                "due_date": subtask_due_str,
                "id": (
                    int(f"{assignment_dict.get('id')}_{i+1}")
                    if assignment_dict.get("id") and str(assignment_dict.get("id")).isdigit()
                    else random.randint(100000, 999999)
                ),
                "priority": assignment_dict.get("priority", "Medium"),
                "group_name": "Subtasks",
                "group_weight": None,
                "grade": None,
                "parent_assignment": assignment_dict.get("id"),
            }
            subtask_dicts.append(subtask_dict)

        # Create each subtask in Notion
        for subtask in subtask_dicts:
            create_subtask_assignment(subtask, config)
        return subtask_dicts
    except Exception as e:
        logger.error(f"Error creating subtasks: {e}")
        return f"Failed to create subtasks: {e}"


@tool
def get_assignment_notes(assignment_name: str, config: RunnableConfig):
    """
    Get notes from an assignment by name

    Args:
        assignment_name: Name of the assignment to retrieve notes from

    Returns:
        Notes associated with the assignment
    """
    user_id = get_user_id_from_config(config)
    notion_api = NotionAPI(user_id=user_id)
    notes = notion_api.get_assignment_notes(assignment_name)

    if notes:
        return notes
    else:
        return f"No assignment found with the name '{assignment_name}'"


tools = [
    retrieve_assignment,
    retrieve_all_assignments,
    get_current_time,
    create_assignment_item,
    get_course_info,
    parse_relative_datetime,
    update_assignment,
    find_assignment,
    create_subtasks,
    get_assignment_notes,
    estimate_completion_time,
]

project_manager_prompt = """

# Project Management Agent for Notion

## Primary Role
You are an agent specialized in managing academic assignments in Notion. You help users track, organize, and complete their academic work efficiently.

## Core Responsibilities
- Understand user requests related to assignment management
- Retrieve information about assignments and courses
- Create and modify assignments and subtasks in Notion
- Estimate completion times and help with time management
- Present information back to the user in a clear, helpful format

## Request Handling Capabilities

### Information Retrieval Tasks:
- Assignments lookup
- Status checking
- Due date inquiries
- Finding relevant course information
- Analyzing workload and scheduling
- Generating reports or summaries

### Modification Tasks:
- Creating new assignments and tasks
- Updating assignment properties (status, priority, due dates)
- Creating subtasks for assignments
- Deleting or archiving completed work
- Reorganizing assignments
                          
## Workflow Process
For complex requests requiring both retrieval and modification:
1. Gather necessary information about existing assignments
2. Process and analyze the retrieved data
3. Make required modifications with precise parameters
4. Verify the changes were made successfully

## Key Data Formats

When working with assignments, ensure proper formatting:
- Assignment dictionary must include 'name' key
- Date formats should follow ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- Required fields for new assignments: name, course_id/course_name
- Optional fields: description, status, due_date, priority

## Common Request Patterns

- "Show my assignments for next week"
- "Create a new essay due Friday"
- "Change the priority of my physics homework"
- "What's due tomorrow?"
- "Add subtasks to my research paper"
- "Move all my completed assignments to Done"

## Error Handling

- If you encounter an error, analyze the cause and retry with adjusted parameters
- If information is ambiguous, ask the user for clarification before proceeding
- For fuzzy matches on assignment names, confirm with the user before making changes
- Verify all operations completed successfully before reporting completion to the user

Always maintain the context of the ongoing task and current state of the user's Notion workspace to provide continuity between operations.
"""
