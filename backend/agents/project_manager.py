# Import minimal functionality needed for the graph node
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all tools from your existing project manager
from agents.project_tools import (
    get_current_time,
    parse_relative_datetime,
    retireve_assignment,
    retrive_all_assignments,
    find_assignment,
    create_assignment_item,
    get_course_info,
    update_assignment,
    create_subtasks,
    get_assignment_notes,
    estimate_completion_time,
)

# Define the tools list
tools = [
    get_current_time, 
    parse_relative_datetime,
    retireve_assignment,
    retrive_all_assignments,
    find_assignment,
    create_assignment_item,
    get_course_info,
    update_assignment,
    create_subtasks,
    get_assignment_notes,
    estimate_completion_time,
]

# Define the same prompt from your existing project manager
prompt = """You are an assistant for managing academic assignments in Notion.

Capabilities:

Retrieve, find, create, and update assignments

Manage course relationships

Instructions:

Use update_assignment with a dictionary containing at least name and any fields to update (e.g., status, priority, due_date).

Use create_assignment_item with required fields: name, course_id or course_name. Optional: description, status, due_date, priority.

For dates, call get_current_time then parse_relative_datetime.

Use find_assignment for fuzzy search; if multiple matches, ask for clarification.

Use retrieve_assignment for details (exact name), or find_assignment first if unsure.

Use get_course_info with course_name or None for all courses.

Use create_subtasks with assignment dict; subtasks should be specific, with staggered due dates before the main assignment.

For common requests:

"Show all assignments" → retrieve_all_assignments

"Update assignment X to status Y" → update_assignment with name="X", status="Y"

"Find biology homework" → find_assignment with "biology homework"

"Create new assignment due tomorrow" → get_current_time, parse_relative_datetime, create_assignment_item

"Set priority of X to high" → update_assignment with name="X", priority="High"

"Create subtasks for X" → create_subtasks with assignment dict

"Estimated time for X?" → find_assignment with "X", then estimate_completion_time

"Get notes for X" → get_assignment_notes with "X"

Always check dictionary formatting before tool use.

If you need information not provided, ask the supervisor for clarification.
"""
