# Import relevant functionality
from langchain_openai import ChatOpenAI
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from notion_client import Client
import os, sys
# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.notion_api import NotionAPI, Assignment
import dotenv
from datetime import datetime
from typing import Dict, Any, Optional, Union
import traceback
import logging
from difflib import get_close_matches

# Setting up the logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the environment variables
dotenv.load_dotenv()

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
def create_assignment_item(assignment_dict):
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

@tool
def estimate_completion_time():
    """
    Estimate total time of completion for each assignment
    """
    pass

@tool
def create_subtasks(assignment):
    """
    Create substasks for each assignment
    """
    pass

@tool
def generate_schedule():# For the future
    """
    Generate a schedule/study plan for each project
    """
    pass

# Create the agent
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Define tools for model

tools = [
    retireve_assignment, 
    retrive_all_assignments, 
    get_current_time, 
    create_assignment_item,
    get_course_info, 
    parse_relative_datetime, 
    update_assignment,
    find_assignment,
    ]

# Create a memory instance
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Define the model prompt

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a powerful assistant for managing academic assignments in Notion.

Your primary capabilities:
1. Retrieving assignments from Notion
2. Finding assignments with fuzzy matching
3. Creating new assignments
4. Updating assignment status and properties
5. Managing course relationships

IMPORTANT USAGE GUIDELINES:

When updating assignments:
- ALWAYS use update_assignment with name and other parameters like priority, status, due_date, etc.
- Dictionary MUST contain the 'name' key with the assignment name
- Include any properties you want to update (status, priority, due_date, etc.)
- Example: {{"name": "Essay on Climate Change", "status": "In Progress", "priority": "High"}}

When creating assignments:
- ALWAYS use create_assignment_item with a complete dictionary of assignment properties
- Required fields: name, course_id or course_name
- Optional fields: description, status, due_date, priority, etc.
- Example: {{"name": "Midterm Research Paper", "course_name": "Biology 101", "due_date": "2025-04-15T23:59:00Z", "priority": "High"}}

When dealing with dates:
- ALWAYS use get_current_time to get the current date/time first
- Use parse_relative_datetime for converting user descriptions to proper dates
- Example flow: get_current_time → parse_relative_datetime("tomorrow at 5pm")

For finding assignments:
- Use find_assignment with partial names for fuzzy matching
- If multiple matches found, ask the user to clarify which one they meant

For retrieving assignment details:
- Use retireve_assignment with the exact assignment name
- If unsure of exact name, use find_assignment first

For finding course names and course IDs:
- Use get_course_info with course_name or None for all courses
- If course_name is not found, return all course names

Common user requests and proper tool usage:
- "Show all my assignments" → use retrive_all_assignments
- "Update assignment X to status Y" → use update_assignment with name="X", status="Y"
- "Find my biology homework" → use find_assignment with "biology homework"
- "Create new assignment due tomorrow" → use get_current_time, then parse_relative_datetime, then create_assignment_item
- "Set priority of X to high" → use update_assignment with name="X", priority="High"

ALWAYS verify you have the correct formatting for dictionary parameters before calling any tool.
"""
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Bind the tools to the model

llm_with_tools = llm.bind_tools(tools)

# Create agent

agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: memory.load_memory_variables({})["chat_history"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

# Add at the end of the file

if __name__ == "__main__":
    print("Notion Project Manager Assistant (Type 'exit' to quit)")
    print("------------------------------------------------------")
    while True:
        user_input = input("\nWhat would you like to do with your Notion assignments? \n")
        if user_input.lower() in ("exit", "quit"):
            break
        try:
            response = agent_executor.invoke({"input": user_input})
            print(f"\nAssistant: {response['output']}")
        except Exception as e:
            print(f"\nError: {str(e)}")
            logger.error(f"Error in CLI: {str(e)}", exc_info=True)