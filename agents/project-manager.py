# Import relevant functionality
from langchain_openai import ChatOpenAI
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from notion_client import Client
import os, sys
# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.notion_api import NotionAPI, Assignment
import dotenv
from datetime import datetime

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
def create_subtasks(assignment):
    """
    Create substasks for each assignment
    """
    pass

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
def get_course_id(course_name: str = None, notion_uuid: str = None):
    """
    Get all course IDs from Notion database

    Agrs:
        course_name: Name of the course to get the ID for (optional)
        notion_uuid: UUID of the course to get the ID for (optional)

    returns a list of course IDs
    """
    if course_name is None and notion_uuid is None:
        raise ValueError("Either course name or notion UUID must be provided")
    
    notion_api = NotionAPI()
    course_id_dict = notion_api._get_course_mapping()
    
    if course_name is None and notion_uuid is not None:
        return course_id_dict.get(notion_uuid)
    else:  # course_name is provided
        course_id = notion_api.get_course_id(course_name)
        for key, value in course_id_dict.items():
            if value == course_id:
                return key
        

@tool
def update_assignment_status(assignment_dict):
    """
    Update a assignment in Notion that follows the imported Assignment schema. 
    Below is an example of the schema:

    assignment = Assignment(
        name="Midterm Research Paper",
        description="<p>Write a 10-page research paper on a topic of your choice.</p>",
        course_id=77456,  # Maps to a Notion course page via course_mapping, obtain this by using get_course_id tool
        status="Not started",
        due_date="2025-04-15T23:59:00Z",
        id=67890,
        priority="High",
        group_name="Papers",
        group_weight=30.0,
        grade=None
    )

    returns the updated assignment object
    """
    notion_api = NotionAPI()
    
    # If we're getting a dictionary (likely from the agent)
    if isinstance(assignment_dict, dict):
        # First retrieve the existing assignment to preserve critical fields
        existing = notion_api.get_assignment_page(assignment_dict.get('name'))
        if not existing:
            raise ValueError(f"Assignment '{assignment_dict.get('name')}' not found")
            
        # Get the existing course relation ID from Notion
        existing_course_id = None
        if existing and 'properties' in existing and 'Course' in existing['properties']:
            relations = existing['properties']['Course']['relation']
            if relations and len(relations) > 0:
                existing_course_id = relations[0]['id']
                print(f"Found existing course ID: {existing_course_id}")
        
        # Create assignment with preserved fields
        assignment = Assignment(
            name=assignment_dict.get('name'),
            description=assignment_dict.get('description', existing['properties'].get('Description', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')),
            # Use existing course ID from Notion if available
            course_id=existing_course_id or assignment_dict.get('course_id'),
            status=assignment_dict.get('status', 'Not started'),
            due_date=existing['properties'].get('Due Date', {}).get('date', {}).get('start') if existing else None,
            id=existing['properties'].get('AssignmentID', {}).get('number') if existing else None,
            priority=existing['properties'].get('Priority', {}).get('select', {}).get('name', 'Medium'),
            group_name=existing['properties'].get('Assignment Group', {}).get('select', {}).get('name'),
            group_weight=existing['properties'].get('Group Weight', {}).get('number'),
            grade=existing['properties'].get('Grade (%)', {}).get('number')
        )
    else:
        assignment = assignment_dict
    
    print(f"Updating assignment with course_id: {assignment.course_id}")
    notion_api.update_assignment(assignment)
    return f"Successfully updated {assignment.name} to status: {assignment.status}"

@tool
def estimate_completion_time():
    """
    Estimate total time of completion for each assignment
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

tools = [retireve_assignment, retrive_all_assignments, get_current_time, create_assignment_item, get_course_id, parse_relative_datetime, update_assignment_status]

# Define the model prompt

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful assistant, you can help me manage my assignments and projects. "
            "IMPORTANT: When dealing with relative dates like 'tomorrow', 'next week', etc., "
            "ALWAYS use the get_current_time tool first to determine the current date before calculating due dates."
            "When the request includes a specific time (like 'at 5pm'), ALWAYS use parse_relative_datetime tool "
            "to correctly handle both the date and time components."
        ),
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
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


list(agent_executor.stream({"input": "I need you to update the Week 6 - Electric Potential (cont.) & Capacitors assignment to 'In progress'"}))


