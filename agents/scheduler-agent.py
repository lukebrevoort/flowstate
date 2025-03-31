from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dataclasses import dataclass

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

# Save credentials
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

# Load credentials
with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)


# Define calendar JSON Interface

@dataclass
class CalendarEvent:
    """
    Represents a Google Calendar event with all relevant details.
    This will include the summary, location, description, start and end times with timezone, and reminders.
    It will include optional parameters such as recurrence, attendees, and Conference Data.
    """
    summary: str
    location: str
    description: str
    start: Dict[str, str] # Should be in the format {'dateTime': '2025-03-27T10:00:00-04:00', 'timeZone': 'America/New_York'}
    end: Dict[str, str] # Should be in the format {'dateTime': '2025-03-27T11:00:00-04:00', 'timeZone': 'America/New_York'}
    reminders: Dict[str, Any] # Should be in the format {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 10}]}
    recurrence: Optional[List[str]] = None
    attendees: Optional[List[str]] = None
    conference_data: Optional[Dict[str, str]] = None

"""
This agent is responsible for scheduling events on the user's Google Calendar.
It uses the Google Calendar API to create events.
Meant to take in user input and create an event on the user's Google Calendar.
This should include times to study 
NEED TO INTEGRATE FOR MULTIPLE GOOGLE CALENDARS. Should be able to specify which calendar to add the event to.
Should also be able to get events from the calendar. Or if not specifed, then all Calendars
"""

"""
event = {
    'summary': 'Team Meeting',
    'location': 'Office',
    'description': 'Discuss project updates.',
    'start': {
        'dateTime': '2025-03-27T18:00:00',
        'timeZone': 'America/New_York',
    },
    'end': {
        'dateTime': '2025-03-27T20:00:00',
        'timeZone': 'America/New_York',
    },
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 10}
        ],
    },
}



event_result = service.events().insert(calendarId='primary', body=event).execute()
print(f"Event created: {event_result['htmlLink']}")

"""

# Define the tools for the agent

@tool
def get_calendar_timezone(calendar_id="primary") -> str:
    """
    Gets the timezone of a specific Google Calendar.

    Args:
    - calendar_id: ID of the calendar to get the timezone for

    Returns:
    - Timezone of the calendar
    """
    try:
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        return calendar['timeZone']
    except Exception as e:
        logger.error(f"Error getting calendar timezone: {str(e)}")
        return f"Error getting calendar timezone: {str(e)}"

@tool
def get_current_time() -> str:
    """
    Gets the current date and time in the format required for Google Calendar API.

    Returns:
    - Current date and time
    """
    try:
        return datetime.now().isoformat()
    except Exception as e:
        logger.error(f"Error getting current time: {str(e)}")
        return f"Error getting current time: {str(e)}"

@tool 
def get_relative_time(start_date: Optional[Union[str, datetime, date]] = None) -> List[Dict[datetime, str]]:
    """
    Generate a mapping of dates to days of the week for a month, starting from the given date.
    
    Args:
    - start_date: Starting date as string or datetime object. If None, defaults to today.
    
    Returns:
    - List of dictionaries mapping datetime objects to day names for the next 30 days
    """
    try:
        # Handle the start date input
        if start_date is None:
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif isinstance(start_date, str):
            try:
                # Try ISO format first
                start = datetime.fromisoformat(start_date)
            except ValueError:
                try:
                    # Try other common formats
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    return [{"error": f"Could not parse date string: {start_date}"}]
        elif isinstance(start_date, datetime):
            start = start_date
        else:  # Assume it's a date
            start = datetime.combine(start_date, datetime.min.time())
        
        # Generate date to day mapping for the next 30 days
        date_mapping = []
        for i in range(30):
            current_date = start + timedelta(days=i)
            day_of_week = current_date.strftime('%A')
            date_str = current_date.strftime('%-m/%-d')  # Format as M/D without leading zeros
            date_mapping.append({current_date: day_of_week})
            
        return date_mapping
        
    except Exception as e:
        logger.error(f"Error in get_relative_time: {str(e)}")
        return [{"error": f"Error generating date mapping: {str(e)}"}]

@tool
def get_calendar_mapping():
    """
    Gets a mapping of all the calendars the user has access to.

    Returns:
    - Mapping of calendar names to calendar IDs
    """
    try:
        results = service.calendarList().list().execute()
        calendars = results.get('items', [])
        calendar_mapping = {}
        for calendar in calendars:
            calendar_mapping[calendar['summary']] = calendar['id']
        return calendar_mapping
    except Exception as e:
        logger.error(f"Error getting calendar mapping: {str(e)}")
        return f"Error getting calendar mapping: {str(e)}"

@tool
def get_events(start_date: str, end_date: str, calendar_id="default") -> List[Dict[str, Any]]:
    """
    Gets all the current events on the user's Google Calendar within a specified time range.

    Args:
    - start_date: Start date of the range
    - end_date: End date of the range
    - calendar_id: ID of the calendar to get events from

    Returns:
    - List of events with all details
    """
    try:
        if not (start_date.endswith('Z') or '+' in start_date or '-' in start_date[10:]):
            start_date = start_date + 'Z'
        if not (end_date.endswith('Z') or '+' in end_date or '-' in end_date[10:]):
            end_date = end_date + 'Z'

        if calendar_id == "default":
            all_events = []

            # Get all the calendars the user has access to
            results = service.calendarList().list().execute()
            calendars = results.get('items', [])
            for calendar in calendars:
                print(f"Checking calendar: {calendar['summary']}")
                calendar_id = calendar['id']
                events_result = service.events().list(calendarId=calendar_id, timeMin=start_date, timeMax=end_date, 
                                                singleEvents=True,
                                                orderBy='startTime').execute()
                
                events = events_result.get('items', [])
                all_events.extend(events)

            return all_events
        else:
            events_result = service.events().list(calendarId=calendar_id, timeMin=start_date, timeMax=end_date, 
                                            singleEvents=True,
                                            orderBy='startTime').execute()
            events = events_result.get('items', [])

            return events
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        return f"Error getting events: {str(e)}"

@tool
def create_event(calendar_event: CalendarEvent, calendar_id: str = 'primary') -> str:
    """
    Creates an event on the user's Google Calendar.
    
    Args:
    - calendar_event: A CalendarEvent object containing all event details
    - calendar_id: ID of the calendar to create the event in (defaults to primary)
    
    Returns:
    - Link to the created event
    """
    try:

        timezone = get_calendar_timezone(calendar_id)
        calendar_event.start['timeZone'] = timezone
        calendar_event.end['timeZone'] = timezone

        # Convert the CalendarEvent object to a dictionary for the API
        event = {
            'summary': calendar_event.summary,
            'location': calendar_event.location,
            'description': calendar_event.description,
            'start': calendar_event.start,
            'end': calendar_event.end,
            'reminders': calendar_event.reminders
        }
        
        # Add optional fields if they exist
        if calendar_event.recurrence:
            event['recurrence'] = calendar_event.recurrence
        if calendar_event.attendees:
            event['attendees'] = [{'email': attendee} for attendee in calendar_event.attendees]
        if calendar_event.conference_data:
            event['conferenceData'] = calendar_event.conference_data
        
        # Create the event
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Event created: {event_result['htmlLink']}"
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        return f"Error creating event: {str(e)}"

@tool
def update_event(event_id: str, event: CalendarEvent, calendar_id: str = 'primary') -> str:
    """
    Updates existing event on the user's Google Calendar with new details.

    Args:
    - event_id: ID of the event to update
    - event: A CalendarEvent object containing updated event details
    - calendar_id: ID of the calendar to update the event in (defaults to primary)

    Returns:
    - Link to the updated event
    """
    try:
        updated_event = {
            'summary': event.summary,
            'location': event.location,
            'description': event.description,
            'start': event.start,
            'end': event.end,
            'reminders': event.reminders
        }

        if event.recurrence:
            updated_event['recurrence'] = event.recurrence
        if event.attendees:
            updated_event['attendees'] = [{'email': attendee} for attendee in event.attendees]
        if event.conference_data:
            updated_event['conferenceData'] = event.conference_data

        # Update the event
        existing_event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Existing event ID: {existing_event['id']}")

        # Make sure your updated_event contains the same ID
        updated_event['id'] = event_id

        # Now try the update
        event_result = service.events().update(calendarId=calendar_id, eventId=event_id, body=updated_event).execute()
        return f"Event updated: {event_result['htmlLink']}"
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        return f"Error updating event: {str(e)}. The event may not exist, or you may not have permission to update it."

@tool
def delete_event(event_id: str, calendar_id: str = 'primary') -> str:
    """
    Deletes an event from the user's Google Calendar.

    Args:
    - event_id: ID of the event to delete
    - calendar_id: ID of the calendar to delete the event from (defaults to primary)

    Returns:
    - Confirmation message
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return f"Event with ID {event_id} was successfully deleted."
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        return f"Error deleting event: {str(e)}. The event may not exist, or you may not have permission to delete it."

@tool
def find_event(event_name: str, timeMin=None, timeMax=None):
    """
    Returns the event with the specified name or keywords within the specified time range.

    Args:
    - event_name: Name of the event or keywords to search for
    - timeMin: Start time of the range (defaults to current time)
    - timeMax: End time of the range (defaults to one week from current time)

    Returns:
    - Event details
    """
    try:
        if timeMin is None:
            timeMin = datetime.now().isoformat()
        if timeMax is None:
            timeMax = (datetime.now() + timedelta(days=7)).isoformat()
        
        # Get all calendars
        calendar_mapping = get_calendar_mapping.invoke({})
        matched_events = []
        
        for calendar_name, calendar_id in calendar_mapping.items():
            events_result = service.events().list(calendarId=calendar_id, q=event_name).execute()
            matched_events.extend(events_result.get('items', []))
        
        if not matched_events:
            return f"No events matching '{event_name}' found in the specified time range."
        
        return matched_events
    except Exception as e:
        logger.error(f"Error finding event: {str(e)}")
        return f"Error finding event: {str(e)}"

@tool
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
    
# Add this after the other tool functions and before the agent creation
def day_name_to_date(day_name: str) -> datetime:
    """
    Helper function to convert day names to actual dates using the next occurrence.
    
    Args:
    - day_name: Name of the day (e.g., "Monday", "Tuesday")
    
    Returns:
    - Datetime object for the next occurrence of that day
    """
    # Get current date
    today = datetime.now().date()
    day_mapping = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    today_weekday = today.weekday()
    target_weekday = day_mapping[day_name.lower()]
    
    # Calculate days to add
    days_ahead = (target_weekday - today_weekday) % 7
    if days_ahead == 0:  # If it's the same day, get next week
        days_ahead = 7
        
    target_date = today + timedelta(days=days_ahead)
    return datetime.combine(target_date, datetime.min.time())

@tool
def validate_date_day_mapping(target_date: Union[str, datetime], day_name: str) -> bool:
    """
    Validates that a specific date corresponds to the expected day of the week.
    
    Args:
    - target_date: The date to validate (string or datetime)
    - day_name: Expected day name (e.g., "Monday", "Tuesday")
    
    Returns:
    - True if the date corresponds to the expected day, False otherwise
    """
    try:
        # Parse date if it's a string
        if isinstance(target_date, str):
            try:
                parsed_date = datetime.fromisoformat(target_date)
            except ValueError:
                try:
                    parsed_date = datetime.strptime(target_date, "%Y-%m-%d")
                except ValueError:
                    return False
        else:
            parsed_date = target_date
        
        # Get the day of week for the date
        actual_day = parsed_date.strftime('%A').lower()
        expected_day = day_name.lower()
        
        return actual_day == expected_day
    except Exception as e:
        logger.error(f"Error validating date-day mapping: {str(e)}")
        return False




# Create the agent
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Define tools for model

tools = [
    get_events,
    get_current_time,
    get_calendar_mapping,
    create_event,
    get_calendar_timezone,
    find_event,
    get_relative_time,
    update_event,
    delete_event,
    find_available_time_slots,
    validate_date_day_mapping,
    ]

# Create a memory instance
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Define the model prompt

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a powerful assistant for managing academic schedules in Google Calendar.

Your primary capabilities:
1. Create, update, and delete events on Google Calendar.
2. Find events by name and retrieve event details.
3. Estimate the time required for an event.
4. Get all events within a specified time range.

IMPORTANT USAGE GUIDELINES:

When getting schedules for a specified timerange, use the following format:
- An example prompt could be: "Show all my schedules from 2025-03-27 to 2025-03-28"
- The tool will return all schedules within the specified time range.
- The time range should be in ISO 8601 format such as 2025-03-27T00:00:00
- for RELATIVE DATES use the get_relative_time tool to convert dates to relative time periods. Usage of the tool could look like: get_relative_time(datetime(2025, 3, 29, 10, 0))
- The timezone should be specified separately, as the Calendar API will handle offsets
- Usage of the tool could look like: get_events('2025-03-27T00:00:00', '2025-03-28T00:00:00')

When getting schedules for a specific calendar, use the following format:
- An example prompt could be: "Show all my schedules from 2025-03-27 to 2025-03-28 for my Work Calendar"
- The tool will return all schedules within the specified time range for the specified calendar.
- First use the get_calendar_mapping tool to get the calendar names and IDs.
- for RELATIVE DATES use the get_relative_time tool to convert dates to relative time periods. Usage of the tool could look like: get_relative_time(datetime(2025, 3, 29, 10, 0))
- The time range should be in ISO 8601 format such as 2025-03-27T00:00:00
- Usage of the tool could look like: get_events('2025-03-27T00:00:00', '2025-03-28T00:00:00', 'c_dcbe20d5d573d8ce1cb90dd97afc9c6da386012257226588ef652b86d0fc3b8b@group.calendar.google.com')

IMPORTANT UPDATE VS CREATE DISTINCTION:
- When user asks to "update" an event, ALWAYS use find_event first to locate the existing event
- If find_event returns no results or errors, inform the user no matching event was found and ask if they want to create a new event instead
- Only proceed to create_event if the user explicitly confirms or originally requested event creation
- When searching with find_event, be precise with date ranges - for example "this Wednesday" means the closest upcoming Wednesday, not next week

When creating an event, use the following format:
- IF YOU ARE ASKED TO "UPDATE" AN EVENT: DO NOT CREATE A NEW EVENT. THIS WILL ALLOW US TO AVOID DUPLICATES
- An example prompt could be: "Create an event for a meeting with the team at 10:00 AM for 1 hour on 2025-03-27"
- The tool will create an event with the specified details.
- ALWAYS double check before creating events that you cross-examine the day/date mappings to ensure the date is correct.
- NEVER CALCULATE DATES INDEPENDANTLY
- for RELATIVE DATES use the get_relative_time tool to convert dates to relative time periods. Usage of the tool could look like: get_relative_time(datetime(2025, 3, 29, 10, 0))
- The default reminder time should ALWAYS be 10 minutes before the event.
- Let the Google Calendar API handle timezone offsets - just specify the dateTime and timeZone separately
- Usage of the tool could look like: create_event(CalendarEvent(summary='Meeting with Team', location='Virtual', description='Discuss project updates.', start={{'dateTime': '2025-03-27T10:00:00', 'timeZone': 'America/New_York'}}, end={{'dateTime': '2025-03-27T11:00:00', 'timeZone': 'America/New_York'}}, reminders={{'useDefault': False, 'overrides': [{{'method': 'email', 'minutes': 10}}]}}))

When updating event, use the following format:
- Use the "find_event" tool to search for the event by name or keywords to get the event ID.
- Once you have the event ID, you can use the "update_event" function to update the event with new details.
- The format for updating an event should be similar to creating an event, but you will need to provide the event ID.
- For example, you can use the "find_event" tool to get the event ID and then call the "update_event" function with the new details.
- An example prompt could be: "Update the meeting with the team on 2025-03-27 to start at 11:00 AM and end at 12:00 PM" -> first use find_event to get the event ID, then call update_event with the new details.

When finding available time slots:
- ALWAYS USE "find_available_time_slots" tool to retrieve all events within a specified time range and retrive the available time.
- Analyze the list of events to find gaps in the schedule where a new event can be scheduled.
- Return the available time slots in a user-friendly format.
- ALWAYS consider the user's existing events and suggest time slots that do not overlap with them.

CRITICAL DATE VALIDATION REQUIREMENTS:
- When working with dates and weekdays, you MUST use the validate_date_day_mapping tool to confirm the day name matches the calendar date
- For example, if a user mentions "this Wednesday", use get_relative_time to get the actual date, then validate_date_day_mapping to confirm it's really Wednesday
- NEVER assume a date-to-day mapping without validation
- For example: validate_date_day_mapping("2025-04-02", "Wednesday") will check if April 2, 2025 is a Wednesday
- If validation fails, explain the discrepancy to the user and suggest the correct date for the day they mentioned
- Add the new validate_date_day_mapping tool to the tools list


Common user requests and proper tool usage:
- "What do I have scheduled for tomorrow?" → get_current_time then get_events from tomorrow's date to the day after
- "Do I have any scheduled events for my Meetings calendar in the next week?" → get_current_time then get_calendar_mapping to map name to ID and then get_events from todays's date to a week after for the Meetings calendar
- "Create an event to study for my Physics Exam tomorrow at 3 PM" → first get the current time then create_event with the specified details for tomorrow at 3 PM
- "Schedule a meeting for this Sunday at 5pm for 2 hours" → first get the current time then use relative_time to find what current day is and then create_event with the specified details for Sunday at 5 PM for 2 hours
- "Update my Advisor Meeting this Wednesday to start at 2 PM and end at 3 PM" → first use find_event to get the event ID for "Advisor Meeting" on Wednesday, then call update_event.
- "What does my available schedule look like for the next 3 days?" → get_current_time then get_events from today to 3 days later and return when the user is available.

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
    print("Google Calendar Agent (Type 'exit' to quit)")
    print("------------------------------------------------------")
    while True:
        user_input = input("\nWhat would you like to do with your Calendar? \n")
        if user_input.lower() in ("exit", "quit"):
            break
        try:
            response = agent_executor.invoke({"input": user_input})
            print(f"\nAssistant: {response['output']}")
        except Exception as e:
            print(f"\nError: {str(e)}")
            logger.error(f"Error in CLI: {str(e)}", exc_info=True)