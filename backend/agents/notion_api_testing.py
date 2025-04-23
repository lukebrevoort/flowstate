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
    
    # Pass datetime objects instead of ISO strings
    current_time = datetime.now()  # Remove isoformat()
    end_time = datetime.now() + timedelta(days=7)  # Remove isoformat()
    
    # Call the function you defined
    assignments = retrive_all_assignments(current_time, end_time)
    
    print(f"Found {len(assignments)} assignments")
    for assignment in assignments:
        print(f"Name: {assignment.name}, Due: {assignment.due_date}, Course: {assignment.course}")

def retrive_all_assignments(current_time: datetime, end_time: datetime):
    """
    Retrieve all assignments from the Notion database with date filtering.
    
    Args:
        current_time: datetime object to filter assignments after this time
        end_time: datetime object to filter assignments before this time
        
    Returns:
        A list of assignment objects with details including name, due date, status, and course
    """
    notion_api = NotionAPI()
    assignment_dicts = notion_api.get_all_assignments(current_time, end_time)
    print(f"Assignment dicts: {assignment_dicts}")

if __name__ == "__main__":
    test_retrieve_all_assignments()