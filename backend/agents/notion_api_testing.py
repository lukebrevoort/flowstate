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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_retrieve_all_assignments():
    """Test function to retrieve all assignments"""
    notion_api = NotionAPI()
    
    # Get current time and end time (7 days from now)
    current_time = datetime.now()
    end_time = current_time + timedelta(days=7)
    
    # Log the date range we're querying
    print(f"Retrieving assignments between {current_time.strftime('%Y-%m-%d')} and {end_time.strftime('%Y-%m-%d')}")
    
    # Call the function with datetime objects
    assignments = retrive_all_assignments(current_time, end_time)
    
    # Print the number of assignments found
    print(f"\nFound {len(assignments)} assignments")
    
    # Print each assignment with formatted date
    for assignment in assignments:
        due_date = assignment['due_date']
        if due_date and 'T' in due_date:
            # Convert ISO format to more readable date
            try:
                dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                formatted_date = due_date
        else:
            formatted_date = due_date
        
        print(f"{formatted_date} - {assignment['name']} ({assignment['course_id']})")

def retrive_all_assignments(current_time, end_time):
    """
    Retrieve all assignments from the Notion database with date filtering.
    
    Args:
        current_time: datetime object to filter assignments after this time
        end_time: datetime object to filter assignments before this time
        
    Returns:
        A list of assignment objects with details including name, due date, status, and course
    """
    notion_api = NotionAPI()
    assignments = notion_api.get_all_assignments(current_time, end_time)
    return assignments

if __name__ == "__main__":
    test_retrieve_all_assignments()