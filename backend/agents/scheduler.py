"""
Google Calendar Scheduler Agent
Handles calendar operations using Google Calendar API with OAuth authentication
"""

import logging
import httpx
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from langchain.agents import tool
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """
    Represents a Google Calendar event with all relevant details.
    """

    summary: str
    location: str
    description: str
    start: Dict[str, str]  # {'dateTime': '2025-03-27T10:00:00-04:00', 'timeZone': 'America/New_York'}
    end: Dict[str, str]  # {'dateTime': '2025-03-27T11:00:00-04:00', 'timeZone': 'America/New_York'}
    reminders: Dict[str, Any]  # {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 10}]}
    recurrence: Optional[List[str]] = None
    attendees: Optional[List[str]] = None
    conference_data: Optional[Dict[str, str]] = None


# Helper function to get user's access token from config
async def get_user_access_token(config: RunnableConfig) -> Optional[str]:
    """
    Extract user's Google Calendar access token from the config

    Args:
        config: LangGraph RunnableConfig containing user information

    Returns:
        Access token string or None if not available
    """
    try:
        from services.google_calendar_oauth import GoogleCalendarOAuthService

        # Extract user_id from config
        configurable = config.get("configurable", {})
        user_id = configurable.get("user_id")

        if not user_id:
            logger.error("No user_id found in config")
            return None

        # Get the OAuth service and retrieve token
        oauth_service = GoogleCalendarOAuthService()
        token_data = await oauth_service.get_user_google_token(user_id)

        if token_data and "access_token" in token_data:
            return token_data["access_token"]
        else:
            logger.warning(f"No Google Calendar token found for user {user_id}")
            return None

    except Exception as e:
        logger.error(f"Error retrieving access token: {str(e)}")
        return None


# Helper function to make authenticated API calls
async def call_calendar_api(
    endpoint: str,
    access_token: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make an authenticated call to Google Calendar API

    Args:
        endpoint: API endpoint (e.g., 'calendars/primary')
        access_token: User's access token
        method: HTTP method (GET, POST, PUT, DELETE)
        params: Query parameters
        json_data: JSON body for POST/PUT requests

    Returns:
        API response as dictionary
    """
    base_url = "https://www.googleapis.com/calendar/v3"
    url = f"{base_url}/{endpoint}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = await client.post(url, headers=headers, params=params, json=json_data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, params=params, json=json_data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        # DELETE requests may not return JSON
        if method == "DELETE":
            return {"status": "deleted", "status_code": response.status_code}

        return response.json()


# Tool functions for the scheduler agent


@tool
async def get_calendar_timezone(calendar_id: str = "primary", config: RunnableConfig = None) -> str:
    """
    Gets the timezone of a specific Google Calendar.

    Args:
        calendar_id: ID of the calendar to get the timezone for
        config: Runtime configuration containing user context

    Returns:
        Timezone of the calendar
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return "Error: User not authenticated with Google Calendar"

        result = await call_calendar_api(f"calendars/{calendar_id}", access_token, method="GET")

        return result.get("timeZone", "UTC")

    except Exception as e:
        logger.error(f"Error getting calendar timezone: {str(e)}")
        return f"Error getting calendar timezone: {str(e)}"


@tool
async def get_current_time() -> str:
    """
    Gets the current date and time in ISO format.

    Returns:
        Current date and time in ISO format
    """
    try:
        return datetime.now().isoformat()
    except Exception as e:
        logger.error(f"Error getting current time: {str(e)}")
        return f"Error getting current time: {str(e)}"


@tool
async def get_relative_time(start_date: Optional[Union[str, datetime]] = None) -> List[Dict[str, str]]:
    """
    Generate a mapping of dates to days of the week for the next 30 days.

    Args:
        start_date: Starting date as string or datetime object. If None, defaults to today.

    Returns:
        List of dictionaries mapping dates to day names
    """
    try:
        # Handle the start date input
        if start_date is None:
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif isinstance(start_date, str):
            try:
                start = datetime.fromisoformat(start_date)
            except ValueError:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    return [{"error": f"Could not parse date string: {start_date}"}]
        else:
            start = start_date

        # Generate date to day mapping for the next 30 days
        date_mapping = []
        for i in range(30):
            current_date = start + timedelta(days=i)
            day_of_week = current_date.strftime("%A")
            date_str = current_date.strftime("%-m/%-d")
            date_mapping.append({date_str: day_of_week})

        return date_mapping

    except Exception as e:
        logger.error(f"Error in get_relative_time: {str(e)}")
        return [{"error": f"Error generating date mapping: {str(e)}"}]


@tool
async def get_calendar_mapping(config: RunnableConfig = None) -> Dict[str, str]:
    """
    Gets a mapping of all the calendars the user has access to.

    Args:
        config: Runtime configuration containing user context

    Returns:
        Mapping of calendar names to calendar IDs
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return {"error": "User not authenticated with Google Calendar"}

        result = await call_calendar_api("users/me/calendarList", access_token, method="GET")

        calendars = result.get("items", [])
        calendar_mapping = {}
        for calendar in calendars:
            calendar_mapping[calendar["summary"]] = calendar["id"]

        return calendar_mapping

    except Exception as e:
        logger.error(f"Error getting calendar mapping: {str(e)}")
        return {"error": f"Error getting calendar mapping: {str(e)}"}


@tool
async def get_events(
    start_date: str, end_date: str, calendar_id: str = "primary", config: RunnableConfig = None
) -> List[Dict[str, Any]]:
    """
    Gets all events on the user's Google Calendar within a specified time range.

    Args:
        start_date: Start date of the range (ISO format)
        end_date: End date of the range (ISO format)
        calendar_id: ID of the calendar to get events from (or "all" for all calendars)
        config: Runtime configuration containing user context

    Returns:
        List of events with all details
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return [{"error": "User not authenticated with Google Calendar"}]

        # Ensure proper ISO8601 format
        def ensure_iso_format(date_str):
            if not date_str:
                return None
            if len(date_str) == 10 and date_str.count("-") == 2:
                return f"{date_str}T00:00:00Z"
            if "T" in date_str and not (date_str.endswith("Z") or "+" in date_str):
                return f"{date_str}Z"
            return date_str

        start_date = ensure_iso_format(start_date)
        end_date = ensure_iso_format(end_date)

        if calendar_id == "all":
            # Get all calendars
            calendar_map = await get_calendar_mapping.ainvoke({}, config=config)
            if "error" in calendar_map:
                return [calendar_map]

            all_events = []
            for cal_id in calendar_map.values():
                try:
                    result = await call_calendar_api(
                        f"calendars/{cal_id}/events",
                        access_token,
                        method="GET",
                        params={"timeMin": start_date, "timeMax": end_date, "singleEvents": True, "orderBy": "startTime"},
                    )
                    all_events.extend(result.get("items", []))
                except Exception:
                    continue

            return all_events
        else:
            result = await call_calendar_api(
                f"calendars/{calendar_id}/events",
                access_token,
                method="GET",
                params={"timeMin": start_date, "timeMax": end_date, "singleEvents": True, "orderBy": "startTime"},
            )

            return result.get("items", [])

    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        return [{"error": f"Error getting events: {str(e)}"}]


@tool
async def create_event(calendar_event: CalendarEvent, calendar_id: str = "primary", config: RunnableConfig = None) -> str:
    """
    Creates an event on the user's Google Calendar.

    Args:
        calendar_event: A CalendarEvent object containing all event details
        calendar_id: ID of the calendar to create the event in
        config: Runtime configuration containing user context

    Returns:
        Link to the created event
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return "Error: User not authenticated with Google Calendar"

        # Get timezone if not provided
        if "timeZone" not in calendar_event.start:
            timezone = await get_calendar_timezone.ainvoke({"calendar_id": calendar_id}, config=config)
            calendar_event.start["timeZone"] = timezone
            calendar_event.end["timeZone"] = timezone

        # Convert CalendarEvent to dictionary
        event = {
            "summary": calendar_event.summary,
            "location": calendar_event.location,
            "description": calendar_event.description,
            "start": calendar_event.start,
            "end": calendar_event.end,
            "reminders": calendar_event.reminders,
        }

        # Add optional fields
        if calendar_event.recurrence:
            event["recurrence"] = calendar_event.recurrence
        if calendar_event.attendees:
            event["attendees"] = [{"email": attendee} for attendee in calendar_event.attendees]
        if calendar_event.conference_data:
            event["conferenceData"] = calendar_event.conference_data

        # Create the event
        result = await call_calendar_api(f"calendars/{calendar_id}/events", access_token, method="POST", json_data=event)

        return f"Event created: {result.get('htmlLink', 'Success')}"

    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        return f"Error creating event: {str(e)}"


@tool
async def update_event(
    event_id: str, event: CalendarEvent, calendar_id: str = "primary", config: RunnableConfig = None
) -> str:
    """
    Updates an existing event on the user's Google Calendar.

    Args:
        event_id: ID of the event to update
        event: A CalendarEvent object containing updated event details
        calendar_id: ID of the calendar containing the event
        config: Runtime configuration containing user context

    Returns:
        Link to the updated event
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return "Error: User not authenticated with Google Calendar"

        # Build updated event
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
        result = await call_calendar_api(
            f"calendars/{calendar_id}/events/{event_id}", access_token, method="PUT", json_data=updated_event
        )

        return f"Event updated: {result.get('htmlLink', 'Success')}"

    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        return f"Error updating event: {str(e)}"


@tool
async def delete_event(
    event_id: str, calendar_id: str = "primary", delete_all_instances: bool = False, config: RunnableConfig = None
) -> str:
    """
    Deletes an event from the user's Google Calendar.

    Args:
        event_id: ID of the event to delete
        calendar_id: ID of the calendar to delete the event from
        delete_all_instances: For recurring events, whether to delete all instances
        config: Runtime configuration containing user context

    Returns:
        Confirmation message
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return "Error: User not authenticated with Google Calendar"

        # Check if this is a recurring event instance
        if "_" in event_id and any(c.isdigit() for c in event_id.split("_")[1]):
            original_event_id = event_id.split("_")[0]

            if delete_all_instances:
                await call_calendar_api(f"calendars/{calendar_id}/events/{original_event_id}", access_token, method="DELETE")
                return f"Recurring event series with ID {original_event_id} was successfully deleted."
            else:
                # Cancel single instance
                event = await call_calendar_api(f"calendars/{calendar_id}/events/{event_id}", access_token, method="GET")
                event["status"] = "cancelled"
                await call_calendar_api(
                    f"calendars/{calendar_id}/events/{event_id}", access_token, method="PUT", json_data=event
                )
                return f"Instance of recurring event with ID {event_id} was successfully cancelled."
        else:
            # Regular event
            await call_calendar_api(f"calendars/{calendar_id}/events/{event_id}", access_token, method="DELETE")
            return f"Event with ID {event_id} was successfully deleted."

    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        return f"Error deleting event: {str(e)}"


@tool
async def find_event(
    event_name: str, time_min: Optional[str] = None, time_max: Optional[str] = None, config: RunnableConfig = None
) -> List[Dict[str, Any]]:
    """
    Finds events matching the specified name or keywords.

    Args:
        event_name: Name of the event or keywords to search for
        time_min: Start time of the range (defaults to current time)
        time_max: End time of the range (defaults to one week from now)
        config: Runtime configuration containing user context

    Returns:
        List of matching events
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return [{"error": "User not authenticated with Google Calendar"}]

        if time_min is None:
            time_min = datetime.now().isoformat()
        if time_max is None:
            time_max = (datetime.now() + timedelta(days=7)).isoformat()

        # Get all calendars
        calendar_map = await get_calendar_mapping.ainvoke({}, config=config)
        if "error" in calendar_map:
            return [calendar_map]

        matched_events = []
        for cal_id in calendar_map.values():
            try:
                result = await call_calendar_api(
                    f"calendars/{cal_id}/events", access_token, method="GET", params={"q": event_name}
                )
                matched_events.extend(result.get("items", []))
            except Exception:
                continue

        if not matched_events:
            return [{"message": f"No events matching '{event_name}' found."}]

        return matched_events

    except Exception as e:
        logger.error(f"Error finding event: {str(e)}")
        return [{"error": f"Error finding event: {str(e)}"}]


@tool
async def find_available_time_slots(
    start_date: str, end_date: str, duration_minutes: int = 60, exclude_early: bool = False, config: RunnableConfig = None
) -> List[str]:
    """
    Finds available time slots in the user's calendar.

    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        duration_minutes: Minimum duration needed for the slot in minutes
        exclude_early: Whether to exclude hours between 12:00 AM and 6:00 AM
        config: Runtime configuration containing user context

    Returns:
        List of available time slots
    """
    try:
        access_token = await get_user_access_token(config)
        if not access_token:
            return ["Error: User not authenticated with Google Calendar"]

        # Ensure proper ISO format
        def ensure_iso_format(date_str):
            if not date_str:
                return None
            if len(date_str) == 10 and date_str.count("-") == 2:
                return f"{date_str}T00:00:00Z"
            if "T" in date_str and not (date_str.endswith("Z") or "+" in date_str):
                return f"{date_str}Z"
            return date_str

        start_date = ensure_iso_format(start_date)
        end_date = ensure_iso_format(end_date)

        # Get all calendar IDs
        calendar_map = await get_calendar_mapping.ainvoke({}, config=config)
        if "error" in calendar_map:
            return [str(calendar_map)]

        calendar_ids = list(calendar_map.values())

        # Get user timezone
        user_timezone = await get_calendar_timezone.ainvoke({"calendar_id": "primary"}, config=config)

        # Query freebusy
        body = {
            "timeMin": start_date,
            "timeMax": end_date,
            "items": [{"id": cal_id} for cal_id in calendar_ids],
            "timeZone": user_timezone,
        }

        result = await call_calendar_api("freeBusy", access_token, method="POST", json_data=body)

        # Process busy slots
        busy_slots = []

        if exclude_early:
            # Add 12 AM - 6 AM slots for each day
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            current_day = datetime(start_dt.year, start_dt.month, start_dt.day, tzinfo=start_dt.tzinfo)
            end_day = datetime(end_dt.year, end_dt.month, end_dt.day, tzinfo=end_dt.tzinfo) + timedelta(days=1)

            while current_day < end_day:
                busy_slots.append({"start": current_day.isoformat(), "end": (current_day + timedelta(hours=6)).isoformat()})
                current_day += timedelta(days=1)

        # Add busy slots from calendars
        for calendar_id, calendar_data in result.get("calendars", {}).items():
            busy_slots.extend(calendar_data.get("busy", []))

        # Sort and merge overlapping slots
        busy_slots.sort(key=lambda x: x["start"])

        if busy_slots:
            merged_slots = []
            current_slot = {
                "start": datetime.fromisoformat(busy_slots[0]["start"].replace("Z", "+00:00")),
                "end": datetime.fromisoformat(busy_slots[0]["end"].replace("Z", "+00:00")),
            }

            for busy in busy_slots[1:]:
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))

                if busy_start <= current_slot["end"]:
                    current_slot["end"] = max(current_slot["end"], busy_end)
                else:
                    merged_slots.append(current_slot)
                    current_slot = {"start": busy_start, "end": busy_end}

            merged_slots.append(current_slot)
            busy_slots = merged_slots
        else:
            busy_slots = []

        # Find free slots
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

            if busy_start > current_time:
                slot_duration = (busy_start - current_time).total_seconds() / 60
                if slot_duration >= duration_minutes:
                    available_slots.append(
                        f"Available from {current_time.strftime('%A, %b %d, %I:%M %p')} "
                        f"to {busy_start.strftime('%A, %b %d, %I:%M %p')}"
                    )

            current_time = max(current_time, busy_end)

        # Check remaining time after last busy slot
        if (end_time - current_time).total_seconds() / 60 >= duration_minutes:
            available_slots.append(
                f"Available from {current_time.strftime('%A, %b %d, %I:%M %p')} "
                f"to {end_time.strftime('%A, %b %d, %I:%M %p')}"
            )

        return available_slots if available_slots else ["No available slots found that match your criteria."]

    except Exception as e:
        logger.error(f"Error finding available time slots: {str(e)}")
        return [f"Error finding available time slots: {str(e)}"]


@tool
async def validate_date_day_mapping(target_date: Union[str, datetime], day_name: str) -> bool:
    """
    Validates that a specific date corresponds to the expected day of the week.

    Args:
        target_date: The date to validate (string or datetime)
        day_name: Expected day name (e.g., "Monday", "Tuesday")

    Returns:
        True if the date corresponds to the expected day, False otherwise
    """
    try:
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

        actual_day = parsed_date.strftime("%A").lower()
        expected_day = day_name.lower()

        return actual_day == expected_day

    except Exception as e:
        logger.error(f"Error validating date-day mapping: {str(e)}")
        return False


# Define tools list for the agent
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


# Define the scheduler agent prompt
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
- ALWAYS make sure the YEAR is correct for ANY created events
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


logger.info("Google Calendar Scheduler agent initialized with OAuth support")
