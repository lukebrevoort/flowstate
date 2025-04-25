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
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from notion_client import Client
import os, sys
# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.notion_api import NotionAPI, Assignment
import dotenv
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
import traceback
import logging
from difflib import get_close_matches

# Setting up the logging
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
            status=assignment_dict.get('select', 'Not started'),  # Changed from 'select' to 'status' to match expected input
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
    
if __name__ == "__main__":
    dotenv.load_dotenv()
    notion_api = NotionAPI()
    assignment = Assignment(
        name="Midterm Research Paper",
        description="<p>Write a 10-page research paper on a topic of your choice.</p>",
        course_id=77456,  # Maps to a Notion course page via course_mapping
        course_name="Sample Course",  # Added course_name
        status="Not started",
        due_date="2025-04-26T23:59:00Z",
        id=67890,
        priority="High",
        group_name="Papers",
        group_weight=30.0,
        grade=None
    )
    notion_api.create_assignment(assignment)