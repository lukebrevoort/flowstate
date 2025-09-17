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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from notion_api import NotionAPI, Assignment
import dotenv
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, Union
import traceback
import logging
from difflib import get_close_matches
import pickle
from typing import Dict, Any, Optional, Union, Tuple, List
from dateutil.relativedelta import relativedelta
from langgraph.graph import StateGraph

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.calendar_auth import get_calendar_service

logger = logging.getLogger(__name__)

# Get an authenticated calendar service
# This happens once when the module is imported

# Currently, avoiding OAuth flow until deployment is ready
"""
try:
    service = get_calendar_service()
    logger.info("Successfully initialized calendar service")
except Exception as e:
    logger.error(f"Failed to initialize calendar service: {str(e)}")
    service = None
"""


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
    start: Dict[str, str]  # Should be in the format {'dateTime': '2025-03-27T10:00:00-04:00', 'timeZone': 'America/New_York'}
    end: Dict[str, str]  # Should be in the format {'dateTime': '2025-03-27T11:00:00-04:00', 'timeZone': 'America/New_York'}
    reminders: Dict[
        str, Any
    ]  # Should be in the format {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 10}]}
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
        return calendar["timeZone"]
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
            day_of_week = current_date.strftime("%A")
            date_str = current_date.strftime("%-m/%-d")  # Format as M/D without leading zeros
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
        calendars = results.get("items", [])
        calendar_mapping = {}
        for calendar in calendars:
            calendar_mapping[calendar["summary"]] = calendar["id"]
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
        # Ensure proper ISO8601 format with timezone
        def ensure_iso_format(date_str):
            if not date_str:
                return None

            # If it's just a date with no time component (YYYY-MM-DD)
            if len(date_str) == 10 and date_str.count("-") == 2:
                # Add time component and UTC designator
                return f"{date_str}T00:00:00Z"

            # If it has time but no timezone designator
            if "T" in date_str and not (date_str.endswith("Z") or "+" in date_str or "-" in date_str[10:]):
                return f"{date_str}Z"

            # Already properly formatted
            return date_str

        start_date = ensure_iso_format(start_date)
        end_date = ensure_iso_format(end_date)

        if calendar_id == "default":
            all_events = []

            # Get all the calendars the user has access to
            results = service.calendarList().list().execute()
            calendars = results.get("items", [])
            for calendar in calendars:
                calendar_id = calendar["id"]
                try:
                    events_result = (
                        service.events()
                        .list(
                            calendarId=calendar_id,
                            timeMin=start_date,
                            timeMax=end_date,
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )

                    events = events_result.get("items", [])
                    all_events.extend(events)
                except Exception as calendar_error:
                    logger.warning(f"Error getting events for calendar {calendar['summary']}: {str(calendar_error)}")
                    continue

            return all_events
        else:
            events_result = (
                service.events()
                .list(calendarId=calendar_id, timeMin=start_date, timeMax=end_date, singleEvents=True, orderBy="startTime")
                .execute()
            )
            events = events_result.get("items", [])

            return events
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        return f"Error getting events: {str(e)}"


@tool
def create_event(calendar_event: CalendarEvent, calendar_id: str = "primary") -> str:
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
        calendar_event.start["timeZone"] = timezone
        calendar_event.end["timeZone"] = timezone

        # Convert the CalendarEvent object to a dictionary for the API
        event = {
            "summary": calendar_event.summary,
            "location": calendar_event.location,
            "description": calendar_event.description,
            "start": calendar_event.start,
            "end": calendar_event.end,
            "reminders": calendar_event.reminders,
        }

        # Add optional fields if they exist
        if calendar_event.recurrence:
            event["recurrence"] = calendar_event.recurrence
        if calendar_event.attendees:
            event["attendees"] = [{"email": attendee} for attendee in calendar_event.attendees]
        if calendar_event.conference_data:
            event["conferenceData"] = calendar_event.conference_data

        # Create the event
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Event created: {event_result['htmlLink']}"
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        return f"Error creating event: {str(e)}"


@tool
def update_event(event_id: str, event: CalendarEvent, calendar_id: str = "primary") -> str:
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
            "summary": event.summary,
            "location": event.location,
            "description": event.description,
            "start": event.start,
            "end": event.end,
            "reminders": event.reminders,
        }

        if event.recurrence:
            updated_event["recurrence"] = event.recurrence
        if event.attendees:
            updated_event["attendees"] = [{"email": attendee} for attendee in event.attendees]
        if event.conference_data:
            updated_event["conferenceData"] = event.conference_data

        # Update the event
        existing_event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Existing event ID: {existing_event['id']}")

        # Make sure your updated_event contains the same ID
        updated_event["id"] = event_id

        # Now try the update
        event_result = service.events().update(calendarId=calendar_id, eventId=event_id, body=updated_event).execute()
        return f"Event updated: {event_result['htmlLink']}"
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        return f"Error updating event: {str(e)}. The event may not exist, or you may not have permission to update it."


@tool
def delete_event(event_id: str, calendar_id: str = "primary", delete_all_instances: bool = False) -> str:
    """
    Deletes an event from the user's Google Calendar.

    Args:
    - event_id: ID of the event to delete (EX: _6tn3ah1g85p3cb9g60o32b9k8gojibb9c8ojabbe75hjcggng)
    - calendar_id: ID of the calendar to delete the event from (defaults to primary)
    - delete_all_instances: For recurring events, whether to delete all instances (True) or just this one (False)

    Returns:
    - Confirmation message
    """
    try:
        # Check if this is a recurring event instance (ID contains underscore and timestamp)
        if "_" in event_id and any(c.isdigit() for c in event_id.split("_")[1]):
            # This appears to be a recurring event instance
            original_event_id = event_id.split("_")[0]

            if delete_all_instances:
                # Delete the entire series by using the original event ID
                service.events().delete(calendarId=calendar_id, eventId=original_event_id).execute()
                return f"Recurring event series with ID {original_event_id} was successfully deleted."
            else:
                # For deleting a single instance, we need to get the instance and mark it as cancelled
                # First try to get the specific instance
                try:
                    # Try to get the specific instance
                    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
                    # Mark it as cancelled
                    event["status"] = "cancelled"
                    service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
                    return f"Instance of recurring event with ID {event_id} was successfully cancelled."
                except Exception as instance_error:
                    # If we can't get the specific instance, try an alternative approach
                    try:
                        # Get the original event
                        original_event = service.events().get(calendarId=calendar_id, eventId=original_event_id).execute()

                        # Extract the instance timestamp
                        instance_time = event_id.split("_")[1]
                        # Format for recurrence ID - might need adjustment based on your actual timestamp format
                        if "T" in instance_time:
                            recurrence_id = instance_time.split("T")[0]
                            instance_datetime = datetime.strptime(instance_time, "%Y%m%dT%H%M%SZ")
                        else:
                            recurrence_id = instance_time
                            instance_datetime = datetime.strptime(instance_time, "%Y%m%d")

                        # Create an exception for this instance
                        exception = {
                            "summary": original_event["summary"],
                            "status": "cancelled",
                            "originalStartTime": {"dateTime": instance_datetime.isoformat() + "Z"},
                            "recurringEventId": original_event_id,
                        }
                        service.events().insert(calendarId=calendar_id, body=exception).execute()
                        return f"Instance of recurring event with ID {event_id} was successfully cancelled."
                    except Exception as e:
                        return f"Error cancelling recurring event instance: {str(e)}"
        else:
            # Regular non-recurring event
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
    - Event details such as summary, location, description, start and end times and Event ID
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
            matched_events.extend(events_result.get("items", []))

        if not matched_events:
            return f"No events matching '{event_name}' found in the specified time range."

        return matched_events
    except Exception as e:
        logger.error(f"Error finding event: {str(e)}")
        return f"Error finding event: {str(e)}"


@tool
def find_available_time_slots(
    start_date: str, end_date: str, duration_minutes: int = 60, exclude_early: bool = False
) -> List[str]:
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
        # Ensure proper ISO8601 format with timezone - use the same helper as in get_events
        def ensure_iso_format(date_str):
            if not date_str:
                return None

            # If it's just a date with no time component (YYYY-MM-DD)
            if len(date_str) == 10 and date_str.count("-") == 2:
                # Add time component and UTC designator
                return f"{date_str}T00:00:00Z"

            # If it has time but no timezone designator
            if "T" in date_str and not (date_str.endswith("Z") or "+" in date_str or "-" in date_str[10:]):
                return f"{date_str}Z"

            # Already properly formatted
            return date_str

        start_date = ensure_iso_format(start_date)
        end_date = ensure_iso_format(end_date)

        # Get all calendars
        calendar_ids = []
        results = service.calendarList().list().execute()
        calendars = results.get("items", [])
        for calendar in calendars:
            calendar_ids.append(calendar["id"])

        # Set up freebusy query
        # Get user's timezone from primary calendar
        user_timezone = service.calendars().get(calendarId="primary").execute()["timeZone"]

        body = {
            "timeMin": start_date,
            "timeMax": end_date,
            "items": [{"id": calendar_id} for calendar_id in calendar_ids],
            "timeZone": user_timezone,
        }

        # Query for busy times
        freebusy_response = service.freebusy().query(body=body).execute()

        # Process the response to find free slots
        busy_slots = []

        if exclude_early:
            # Add busy slots from 12:00 AM to 6:00 AM for each day in the range
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            # Get the starting date at midnight
            current_day = datetime(start_dt.year, start_dt.month, start_dt.day, tzinfo=start_dt.tzinfo)
            end_day = datetime(end_dt.year, end_dt.month, end_dt.day, tzinfo=end_dt.tzinfo) + timedelta(days=1)

            # For each day in the range
            while current_day < end_day:
                busy_slots.append({"start": current_day.isoformat(), "end": (current_day + timedelta(hours=6)).isoformat()})
                current_day += timedelta(days=1)

        # Add all busy slots from calendars
        for calendar_id, calendar_data in freebusy_response["calendars"].items():
            busy_slots.extend(calendar_data.get("busy", []))

        # Sort busy slots by start time
        busy_slots.sort(key=lambda x: x["start"])

        # Merge overlapping busy slots
        if busy_slots:
            merged_slots = []
            current_slot = {
                "start": datetime.fromisoformat(busy_slots[0]["start"].replace("Z", "+00:00")),
                "end": datetime.fromisoformat(busy_slots[0]["end"].replace("Z", "+00:00")),
            }

            for busy in busy_slots[1:]:
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))

                # If this busy slot overlaps with the current merged slot, extend the end time
                if busy_start <= current_slot["end"]:
                    current_slot["end"] = max(current_slot["end"], busy_end)
                else:
                    # No overlap, add the current slot to merged list and start a new one
                    merged_slots.append(current_slot)
                    current_slot = {"start": busy_start, "end": busy_end}

            # Add the last slot
            merged_slots.append(current_slot)

            # Convert merged slots to datetime objects
            busy_slots = merged_slots
        else:
            busy_slots = []

        # Find gaps between busy slots (free time)
        available_slots = []
        current_time = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        for busy in busy_slots:
            busy_start = (
                busy["start"]
                if isinstance(busy["start"], datetime)
                else datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
            )
            busy_end = (
                busy["end"]
                if isinstance(busy["end"], datetime)
                else datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
            )

            # Add a free slot if there's enough time before the busy slot
            if busy_start > current_time:
                slot_duration = (busy_start - current_time).total_seconds() / 60
                if slot_duration >= duration_minutes:
                    # Format with clear date distinction
                    start_format = "%A, %b %d, %I:%M %p"
                    end_format = "%A, %b %d, %I:%M %p"
                    available_slots.append(
                        f"Available from {current_time.strftime(start_format)} to {busy_start.strftime(end_format)}"
                    )

            # Move current time to the end of the busy slot
            current_time = max(current_time, busy_end)

        # Check if there's free time after the last busy slot
        if (end_time - current_time).total_seconds() / 60 >= duration_minutes:
            start_format = "%A, %b %d, %I:%M %p"
            end_format = "%A, %b %d, %I:%M %p"
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
    day_mapping = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}

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
        actual_day = parsed_date.strftime("%A").lower()
        expected_day = day_name.lower()

        return actual_day == expected_day
    except Exception as e:
        logger.error(f"Error validating date-day mapping: {str(e)}")
        return False


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

# Define the model prompt
scheduler_prompt = """
# Google Calendar Management Agent

## Primary Role
You are an agent specialized in managing academic schedules in Google Calendar. You can both retrieve calendar information and modify calendar events.

## Core Responsibilities
- Understand user requests related to calendar management
- Retrieve calendar information when needed
- Create, update, and delete calendar events as requested
- Present information back to the user in a clear, helpful format

## Request Handling Guidelines

### Information Retrieval Tasks:
- View schedules for specific time periods
- Find events by name or keywords
- Check availability for specific days/times
- Get calendar mapping information
- Analyze schedule workload and conflicts
- Validate date-day mappings

### Modification Tasks:
- Creating new calendar events
- Updating event properties (time, location, description)
- Deleting or canceling events
- Setting up event reminders
- Finding available time slots for new events

## Critical Date Handling Requirements

- Always validate date-day mappings before calendar operations
- For relative dates (e.g., "tomorrow", "next Wednesday"), get precise dates before operations
- Never assume date calculations without verification
- ALWAYS make sure the YEAR is correct for ANY created events.
- ISO 8601 format required for all date-time values (YYYY-MM-DDTHH:MM:SS)
- Let Google Calendar API handle timezone offsets

## Common Request Patterns

- "What's on my schedule tomorrow?" - Retrieve events for tomorrow
- "Create a study session for Friday at 3pm" - Create new calendar event
- "Move my advisor meeting to 2pm" - Find meeting event and update its time
- "Am I free next Tuesday afternoon?" - Check availability for specified time
- "When can I schedule a 2-hour meeting this week?" - Find available time slots
- "Delete my study group meeting" - Find and remove specified event

## Error Handling

- If an operation encounters an error, analyze the cause and retry with adjusted parameters
- For event not found errors, confirm with the user before creating new events
- Validate date-day mappings before any calendar operations
- Verify all operations completed successfully before reporting completion to the user

## CRITICAL: Tool Response Handling
- DO NOT interpret or analyze tool results yourself
- Simply call the appropriate tools to retrieve information or perform actions
- Return the raw tool results to the user without additional analysis
- The forwarding tool will handle interpretation and presentation of results
- Your job is ONLY to determine which tools to call and with what parameters

Always maintain context of the ongoing task and operate based on the user's requests. DO NOT add your own interpretation to tool outputs.
"""
