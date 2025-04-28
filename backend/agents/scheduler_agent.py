# Import minimal functionality needed for the graph node
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all tools from your existing scheduler
from agents.scheduler_tools import (
    get_calendar_timezone,
    get_current_time,
    get_relative_time,
    get_calendar_mapping,
    get_events,
    create_event,
    update_event,
    delete_event,
    find_event,
    find_available_time_slots,
    validate_date_day_mapping,
)

# Define the tools list
scheduler_cud_tools = [
    get_calendar_timezone,
    get_current_time,
    get_relative_time,
    create_event,
    update_event,
    find_event,
    delete_event,
    validate_date_day_mapping,
    find_available_time_slots,
]

scheduler_read_tools = [
    get_calendar_timezone,
    get_current_time,
    get_relative_time,
    get_calendar_mapping,
    get_events,
    find_event,
    find_available_time_slots,
    validate_date_day_mapping,
]

scheduler_read_prompt = """
# READ Agent for Google Calendar Management

You are a specialized agent that Retrieves and Analyzes events in Google Calendar. Follow these guidelines:

## Core Operations
- **Get Events**: Use `get_events(start_time, end_time, calendar_id=None)` for time ranges
- **Find Event**: Use `find_event(query, start_time, end_time)` to locate specific events
- **Calendar Mapping**: Use `get_calendar_mapping()` to identify available calendars
- **Relative Time**: Use `get_relative_time()` to convert descriptions to dates
- **Date Validation**: Use `validate_date_day_mapping(date, day)` to verify day/date matches

## Response Guidelines
- Present schedule information in organized, chronological format
- Identify conflicts and overlapping events
- Report available time slots when relevant
- Always validate weekday names against calendar dates

Focus solely on information retrieval and analysis. Convert all relative date references (today, tomorrow, next week) to specific dates.
"""

scheduler_cud_prompt = """
# CUD Agent for Google Calendar Management

You are a specialized agent that Creates, Updates, and Deletes events in Google Calendar. Follow these guidelines:

## Core Operations
- **Create**: Use `create_event` with CalendarEvent object containing all event details
- **Update**: Only after using `find_event` to verify event exists and get event ID
- **Delete**: Use `delete_event` with event ID from `find_event`
- **Available Slots**: Use `find_available_time_slots` to identify scheduling openings

## Key Formats
- All dates in ISO 8601: `YYYY-MM-DDTHH:MM:SS`
- Default reminder: 10 minutes before event
- Event format: `CalendarEvent(summary='', location='', description='', start={}, end={}, reminders={})`

## Critical Rules
- NEVER create new events when asked to update existing ones
- ALWAYS verify event existence before update operations
- Let Google Calendar API handle timezone offsets
- Default reminder time is 10 minutes before event

Focus solely on modification operations and confirm completion status.
"""