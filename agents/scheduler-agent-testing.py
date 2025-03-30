from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, Union
import traceback
import logging
from difflib import get_close_matches
import pickle
from typing import Dict, Any, Optional, Union, Tuple, List
from dateutil.relativedelta import relativedelta

# Setting up the logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the environment variables
dotenv.load_dotenv()
"""


# Specify the scopes you need
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Authenticate using OAuth flow
flow = InstalledAppFlow.from_client_secrets_file('OAuth Client ID JSON.json', SCOPES)
creds = flow.run_local_server(port=0)

# Build the service
service = build('calendar', 'v3', credentials=creds)

# Save credentials
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

# Load credentials
with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

"""

def get_relative_time(target_date: str) -> str:
    """
    Used to map dates (Such as 03/28/2025) to days of the week (Friday) or relative time periods (Today).
    Will be used to provide more user-friendly responses to queries.

    Returns:
    - Relative time period
    """
    now = datetime.now()
    today = date.today()
    target = target_date.date() if isinstance(target_date, datetime) else target_date
    delta = relativedelta(target, today)
    
    day_of_week = target_date.strftime('%A')
    
    if target == today:
        return "Today"
    elif target == today + relativedelta(days=1):
        return "Tomorrow"
    elif target == today - relativedelta(days=1):
        return "Yesterday"
    elif 0 < delta.days < 7:
        return f"This {day_of_week}"
    elif -7 < delta.days < 0:
        return f"Last {day_of_week}"
    elif delta.days == 7:
        return f"Next {day_of_week}"
    elif delta.months == 0 and delta.years == 0:
        return f"{abs(delta.days)} days {'from now' if delta.days > 0 else 'ago'}"
    elif delta.years == 0:
        return f"{abs(delta.months)} months {'from now' if delta.months > 0 else 'ago'}"
    else:
        return f"{abs(delta.years)} years {'from now' if delta.years > 0 else 'ago'}"

tomorrow = datetime(2025, 3, 29, 10, 0)
next_week = datetime(2025, 4, 4, 15, 30)
last_month = datetime(2025, 2, 15, 9, 0)

print(get_relative_time(last_month))
'''
# Output: {'Work': 'work_calendar_id', 'Personal': 'personal_calendar_id'}
'''