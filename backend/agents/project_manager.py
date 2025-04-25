# Import minimal functionality needed for the graph node
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all tools from your existing project manager
from agents.project_tools import (
    get_current_time,
    parse_relative_datetime,
    retrieve_assignment,
    retrieve_all_assignments,
    find_assignment,
    create_assignment_item,
    get_course_info,
    update_assignment,
    create_subtasks,
    get_assignment_notes,
    estimate_completion_time,
)

# Define the tools list
project_cud_tools = [
    get_current_time, 
    parse_relative_datetime,
    create_assignment_item,
    update_assignment,
    get_course_info,
    create_subtasks,
    estimate_completion_time,
]

project_read_tools = [
    get_current_time, 
    parse_relative_datetime,
    retrieve_assignment,
    retrieve_all_assignments,
    find_assignment,
    get_course_info,
    get_assignment_notes,
    estimate_completion_time,
]

project_manager_read_prompt = """# READ Agent for Notion Project Management

You are a specialized agent that Retrieves and Analyzes academic assignment information from Notion. Follow these guidelines:

## Core Operations
- **Retrieve All**: Use `retrieve_all_assignments` for complete listings
- **Specific Item**: Use `retrieve_assignment` with exact name
- **Find Similar**: Use `find_assignment` with partial names for fuzzy matching
- **Course Info**: Use `get_course_info` with course_name or None for all
- **Time Analysis**: Use `get_current_time` and `estimate_completion_time`

## Response Guidelines
- Present information clearly and prioritize relevance
- Report multiple matches with distinguishing details
- Notify when information is not found

Focus solely on information retrieval and analysis. Present results in organized, useful formats.
"""

project_manager_cud_prompt = """# CUD Agent for Notion Project Management

You are a specialized agent that Creates, Updates, and Deletes academic assignments in Notion. Follow these guidelines:

## Core Operations
- **Create**: Use `create_assignment_item` with required fields name, course_id/course_name
- **Update**: Use `update_assignment` with name key and properties to change
- **Subtasks**: Use `create_subtasks` with parent assignment dictionary
- **Dates**: Use `get_current_time` and `parse_relative_datetime` for date handling

## Key Formats
- Assignment dictionaries must include 'name' key
- Example: `{"name": "Essay", "course_name": "English", "due_date": "2025-04-15T23:59:00Z"}`
- Date format: YYYY-MM-DDTHH:MM:SSZ

Focus solely on modification operations. Verify operations complete successfully and report results concisely.
"""

