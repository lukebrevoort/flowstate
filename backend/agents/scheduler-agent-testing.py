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


# Specify the scopes you need
SCOPES = ['https://www.googleapis.com/auth/calendar']

oauth_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'OAuth Client ID JSON.json')

# Authenticate using OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(oauth_file_path, SCOPES)
creds = flow.run_local_server(port=0)

# Build the service
service = build('calendar', 'v3', credentials=creds)




def find_available_time_slots(start_date: str, end_date: str, duration_minutes: int = 60, exclude_early: bool = False) -> List[str]:
    """
    Finds available time slots in the user's calendar using Google Calendar's freebusy API.
    
    Args:
    - start_date: Start date in ISO format
    - end_date: End date in ISO format
    - duration_minutes: Minimum duration needed for the slot in minutes (default 60)
    - exclude_early: Boolean to check if the user wants to filter time slots of exclude the hours of 12:00 AM to 6:00 AM (Default False)

    Returns:
    - List of available time slots
    """
    try:
        if not (start_date.endswith('Z') or '+' in start_date or '-' in start_date[10:]):
            start_date = start_date + 'Z'
        if not (end_date.endswith('Z') or '+' in end_date or '-' in end_date[10:]):
            end_date = end_date + 'Z'
        
        # Get all calendars
        calendar_ids = []
        results = service.calendarList().list().execute()
        calendars = results.get('items', [])
        for calendar in calendars:
            calendar_ids.append(calendar['id'])
        
        # Set up freebusy query
        # Get user's timezone from primary calendar
        user_timezone = service.calendars().get(calendarId='primary').execute()['timeZone']
        
        body = {
            "timeMin": start_date,
            "timeMax": end_date,
            "items": [{"id": calendar_id} for calendar_id in calendar_ids],
            "timeZone": user_timezone
        }
        
        # Query for busy times
        freebusy_response = service.freebusy().query(body=body).execute()
        
        # Process the response to find free slots
        busy_slots = []
        
        if exclude_early:
            # Add busy slots from 12:00 AM to 6:00 AM for each day in the range
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            # Get the starting date at midnight
            current_day = datetime(start_dt.year, start_dt.month, start_dt.day, tzinfo=start_dt.tzinfo)
            end_day = datetime(end_dt.year, end_dt.month, end_dt.day, tzinfo=end_dt.tzinfo) + timedelta(days=1)

            # For each day in the range
            while current_day < end_day:
                busy_slots.append({
                    'start': current_day.isoformat(),
                    'end': (current_day + timedelta(hours=6)).isoformat()
                })
                current_day += timedelta(days=1)
                
        # Add all busy slots from calendars
        for calendar_id, calendar_data in freebusy_response['calendars'].items():
            busy_slots.extend(calendar_data.get('busy', []))
        
        # Sort busy slots by start time
        busy_slots.sort(key=lambda x: x['start'])
        
        # Merge overlapping busy slots
        if busy_slots:
            merged_slots = []
            current_slot = {
                'start': datetime.fromisoformat(busy_slots[0]['start'].replace('Z', '+00:00')),
                'end': datetime.fromisoformat(busy_slots[0]['end'].replace('Z', '+00:00'))
            }
            
            for busy in busy_slots[1:]:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                
                # If this busy slot overlaps with the current merged slot, extend the end time
                if busy_start <= current_slot['end']:
                    current_slot['end'] = max(current_slot['end'], busy_end)
                else:
                    # No overlap, add the current slot to merged list and start a new one
                    merged_slots.append(current_slot)
                    current_slot = {'start': busy_start, 'end': busy_end}
            
            # Add the last slot
            merged_slots.append(current_slot)
            
            # Convert merged slots to datetime objects
            busy_slots = merged_slots
        else:
            busy_slots = []
        
        # Find gaps between busy slots (free time)
        available_slots = []
        current_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        for busy in busy_slots:
            busy_start = busy['start'] if isinstance(busy['start'], datetime) else datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
            busy_end = busy['end'] if isinstance(busy['end'], datetime) else datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
            
            # Add a free slot if there's enough time before the busy slot
            if busy_start > current_time:
                slot_duration = (busy_start - current_time).total_seconds() / 60
                if slot_duration >= duration_minutes:
                    # Format with clear date distinction
                    start_format = '%A, %b %d, %I:%M %p'
                    end_format = '%A, %b %d, %I:%M %p'
                    available_slots.append(f"Available from {current_time.strftime(start_format)} to {busy_start.strftime(end_format)}")
            
            # Move current time to the end of the busy slot
            current_time = max(current_time, busy_end)
        
        # Check if there's free time after the last busy slot
        if (end_time - current_time).total_seconds() / 60 >= duration_minutes:
            start_format = '%A, %b %d, %I:%M %p'
            end_format = '%A, %b %d, %I:%M %p'
            available_slots.append(f"Available from {current_time.strftime(start_format)} to {end_time.strftime(end_format)}")
        
        return available_slots if available_slots else ["No available slots found that match your criteria."]
        
    except Exception as e:
        logger.error(f"Error finding available time slots: {str(e)}")
        return [f"Error finding available time slots: {str(e)}"]

# Test data for find_available_time_slots
start_date = (datetime.now()).isoformat() + 'Z'
end_date = (datetime.now() + timedelta(days=4)).isoformat() + 'Z'
duration = 60  # minutes

print("Testing with:")
print(f"Start date: {start_date}")
print(f"End date: {end_date}")
print(f"Duration: {duration} minutes")

available_slots = find_available_time_slots(start_date, end_date, duration)
print("\nAvailable time slots:")
for slot in available_slots:
    print(f"- {slot}")
'''
# Output: {'Work': 'work_calendar_id', 'Personal': 'personal_calendar_id'}
'''