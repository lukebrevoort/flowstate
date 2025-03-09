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


print(update_assignment({'name': 'chapter 24', 'priority': 'High'}))