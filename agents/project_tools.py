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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.notion_api import NotionAPI, Assignment
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from difflib import get_close_matches

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

# Define the tools

@tool
def get_current_time():
    """
    Get the current date and time.
    
    Returns the current date and time in a formatted string.
    """
    notion_api = NotionAPI()
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
    from dateparser import parse
    import re
    
    current_time = datetime.now()
    
    # Try to extract time information
    time_pattern = r'at\s+(\d+)(?::(\d+))?\s*(am|pm|AM|PM)'
    time_match = re.search(time_pattern, date_description)
    
    # First parse the date
    parsed_date = parse(date_description, settings={'RELATIVE_BASE': current_time})
    
    # If we found specific time information, apply it
    if time_match and parsed_date:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        am_pm = time_match.group(3).lower()
        
        # Convert to 24-hour format
        if am_pm == 'pm' and hour < 12:
            hour += 12
        elif am_pm == 'am' and hour == 12:
            hour = 0
            
        # Set the time component
        parsed_date = parsed_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if parsed_date:
        return parsed_date.isoformat()
    return None

@tool
def retireve_assignment(assignment_name: str):
    """
    Retrieve assignments from a given Notion database

    returns a object with all assignment information included
    """
    notion_api = NotionAPI()
    assignment = notion_api.get_assignment_page(assignment_name)
    return assignment

@tool
def retrive_all_assignments():
    """
    Retrieve all assignments from the given Notion database that are either submitted or not submitted based on parameter

    returns a list of assignment objects with name, due date, status, and course
    """
    notion_api = NotionAPI()
    assignments = notion_api.get_all_assignments()
    return assignments

@tool
def find_assignment(query: str):
    """
    Find an assignment using fuzzy matching on the name.
    
    Args:
        query: Text to search for in assignment names
        
    Returns:
        The best matching assignment or a list of possible matches
    """
    notion_api = NotionAPI()
    assignments = notion_api.get_all_assignments()
    
    # Extract just the names for matching
    names = [a['name'] for a in assignments]
    
    # If exact match exists, return it
    if query in names:
        for assignment in assignments:
            if assignment['name'] == query:
                return assignment
    
    # Try fuzzy matching
    matches = get_close_matches(query, names, n=3, cutoff=0.6)
    
    if not matches:
        return f"No assignments found matching '{query}'"
    
    if len(matches) == 1:
        # Return the single match
        for assignment in assignments:
            if assignment['name'] == matches[0]:
                return assignment
    
    # Return possible matches for clarification
    return {
        "message": f"Multiple assignments found matching '{query}'",
        "matches": matches
    }

@tool
def create_assignment_item(assignment_dict: Dict[str, Any]):
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
    if isinstance(assignment_dict, dict):
        assignment = Assignment(
            name=assignment_dict.get('name'),
            description=assignment_dict.get('description'),
            course_id=assignment_dict.get('course_id'),
            course_name=assignment_dict.get('course_name'),
            status=assignment_dict.get('status', 'Not started'),
            due_date=assignment_dict.get('due_date'),
            id=assignment_dict.get('id'),
            priority=assignment_dict.get('priority', 'Medium'),
            group_name=assignment_dict.get('group_name'),
            group_weight=assignment_dict.get('group_weight'),
            grade=assignment_dict.get('grade')
        )
    else:
        assignment = assignment_dict
        
    notion_api = NotionAPI()
    print(f"Creating assignment with due date: {assignment.due_date}"); notion_api.create_assignment(assignment)
    return assignment

@tool
def get_course_info(course_name: str = None):
    """
    Get course information from Notion database.
    
    Args:
        course_name: (Optional) Name or code of the course to search for
        
    Returns:
        If course_name is provided and found: Course UUID
        If course_name is provided but not found: List of all course names
        If course_name is not provided: List of all course names
    """
    notion_api = NotionAPI()
    
    # If no course name provided, return all course names
    if not course_name:
        course_name_dict = notion_api._get_course_name_mapping()
        return list(course_name_dict.keys())
    
    # Try to get the course ID
    course_id = notion_api.get_course_id(course_name)
    
    # If found, return the Canvas ID
    if course_id:
        course_id_dict = notion_api._get_course_mapping()
        for key, value in course_id_dict.items():
            if value == course_id:
                return key
    
    # If not found, return all course names
    course_name_dict = notion_api._get_course_name_mapping()
    return list(course_name_dict.keys())

@tool
def update_assignment(name: str, priority: str = None, status: str = None, 
                      due_date: str = None, description: str = None) -> str:
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
    # Build the dictionary from the individual parameters
    assignment_dict = {'name': name}
    if priority is not None:
        assignment_dict['priority'] = priority
    if status is not None:
        assignment_dict['status'] = status
    if due_date is not None:
        assignment_dict['due_date'] = due_date
    if description is not None:
        assignment_dict['description'] = description
        
    # Initialize the NotionAPI
    notion_api = NotionAPI()
    try:
        # Attempt to update the assignment
        updated_assignment = notion_api.update_assignment(assignment_dict)
        return f"Assignment updated successfully."
    except Exception as e:
        # Log the error and return a message
        logger.error(f"Error updating assignment: {e}")
        return f"Failed to update assignment: {e}"
    

time_prompt = PromptTemplate.from_template("""
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
""")

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

    estimated_time = chain.invoke({
        "assignment": assignment_dict['name'],
        "due_date": assignment_dict['due_date'],
        "status": assignment_dict.get('status', 'Not started'),
        "description": assignment_dict.get('description', ''),
        "notes": get_assignment_notes(assignment_dict['name'])
    })

    if estimated_time:
        return estimated_time.content
    else:
        logger.error("Failed to estimate completion time.")
        return "Failed to estimate completion time."

    
    pass

subtask_prompt = PromptTemplate.from_template("""
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
""")

def create_subtask_assignment(assignment_dict):
    """
    Create a subtask in Notion that follows the imported Assignment schema. 
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
    if isinstance(assignment_dict, dict):
        assignment = Assignment(
            name=assignment_dict.get('name'),
            description=assignment_dict.get('description'),
            course_id=assignment_dict.get('course_id'),
            course_name=assignment_dict.get('course_name'),
            status=assignment_dict.get('status', 'Not started'),
            due_date=assignment_dict.get('due_date'),
            id=assignment_dict.get('id'),
            priority=assignment_dict.get('priority', 'Medium'),
            group_name=assignment_dict.get('group_name'),
            group_weight=assignment_dict.get('group_weight'),
            grade=assignment_dict.get('grade')
        )
    else:
        assignment = assignment_dict
        
    notion_api = NotionAPI()
    print(f"Creating assignment with due date: {assignment.due_date}"); notion_api.create_assignment(assignment)
    return assignment

@tool
def create_subtasks(assignment_dict):
    """
    Create subtasks for a given assignment and add them to Notion.

    Args:
        assignment: Dictionary containing assignment details.

    Returns:
        List of subtask dictionaries ready to be created in Notion.
    """
    try:
        chain = subtask_prompt | llm

        if 'current_date' not in assignment_dict:
            current_time = datetime.now()
            assignment_dict['current_date'] = current_time.isoformat()
        
        # Get subtasks from LLM
        subtasks_result = chain.invoke({
            "assignment": assignment_dict['name'],
            "current_date": assignment_dict['current_date'],
            "due_date": assignment_dict['due_date'],
            "status": assignment_dict.get('status', 'Not started'),
            "description": assignment_dict.get('description', ''),
            "notes": get_assignment_notes(assignment_dict['name'])
        })
        
        # Parse the LLM output into a list of subtask names
        subtask_names = subtasks_result.content.strip().split('\n')
        
        # Calculate time gap for evenly spaced subtasks
        from dateutil import parser
        import random
        import pytz
        from datetime import datetime, time
        
        # Parse dates and ensure both have timezone information
        start_date = parser.parse(assignment_dict['current_date'])
        due_date = parser.parse(assignment_dict['due_date'])
            
        # Calculate the number of days between start and due date
        days_span = (due_date.date() - start_date.date()).days
        
        # Calculate time span with consistent timezone information
        time_span = (due_date - start_date).total_seconds()
        time_step = time_span / (len(subtask_names) + 1)
        
        # Create a list of dictionaries for each subtask
        subtask_dicts = []
        for i, subtask_name in enumerate(subtask_names):
            subtask_due = start_date + timedelta(seconds=(i+1) * time_step)
            
            # Round to the nearest half hour
            minute = subtask_due.minute
            if minute < 15:
                # Round down to the hour
                subtask_due = subtask_due.replace(minute=0, second=0, microsecond=0)
            elif 15 <= minute < 45:
                # Round to half past the hour
                subtask_due = subtask_due.replace(minute=30, second=0, microsecond=0)
            else:
                # Round up to the next hour
                subtask_due = subtask_due.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            # Format the datetime as an ISO string with timezone
            if subtask_due.tzinfo is None:
                subtask_due_str = subtask_due.isoformat() + 'Z'
            else:
                subtask_due_str = subtask_due.isoformat()
            
            # Create subtask dictionary with necessary fields
            subtask_dict = {
                'name': f"{subtask_name} - {assignment_dict['name']}",
                'description': f"<p>Subtask for: {assignment_dict['name']}</p>",
                'course_id': assignment_dict.get('course_id'),
                'course_name': assignment_dict.get('course_name'),
                'status': 'Not started',
                'due_date': subtask_due_str,
                'id': int(f"{assignment_dict.get('id')}_{i+1}") if assignment_dict.get('id') and str(assignment_dict.get('id')).isdigit() else random.randint(100000, 999999),              
                'priority': assignment_dict.get('priority', 'Medium'),
                'group_name': "Subtasks",
                'group_weight': None,
                'grade': None,
                'parent_assignment': assignment_dict.get('id')
            }
            subtask_dicts.append(subtask_dict)
        
        # Create each subtask in Notion
        for subtask in subtask_dicts:
            create_subtask_assignment(subtask)
        return subtask_dicts
    except Exception as e:
        logger.error(f"Error creating subtasks: {e}")
        return f"Failed to create subtasks: {e}"

@tool
def get_assignment_notes(assignment_name: str):
    """
    Get notes from an assignment by name
    
    Args:
        assignment_name: Name of the assignment to retrieve notes from
        
    Returns:
        Notes associated with the assignment
    """
    notion_api = NotionAPI()
    notes = notion_api.get_assignment_notes(assignment_name)
    
    if notes:
        return notes
    else:
        return f"No assignment found with the name '{assignment_name}'"



tools = [
    retireve_assignment, 
    retrive_all_assignments, 
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