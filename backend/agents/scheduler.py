# TEMPORARILY COMMENTED OUT UNTIL GOOGLE OAUTH IS PROPERLY INITIALIZED
# This file contains Google Calendar OAuth dependencies that cause undefined variable errors
# when OAuth is not configured. Restore from scheduler.py.backup when ready.

"""
Google Calendar Scheduler Agent - TEMPORARILY DISABLED

This agent is responsible for scheduling events on the user's Google Calendar.
It uses the Google Calendar API to create events.
Currently disabled due to incomplete Google OAuth setup.

To restore: mv scheduler.py.backup scheduler.py after OAuth is configured.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """
    Represents a Google Calendar event with all relevant details.
    Currently disabled - placeholder only.
    """

    summary: str
    location: str
    description: str
    start: Dict[str, str]
    end: Dict[str, str]
    reminders: Dict[str, Any]
    recurrence: Optional[List[str]] = None
    attendees: Optional[List[str]] = None
    conference_data: Optional[Dict[str, str]] = None


# Placeholder functions to prevent import errors
def get_calendar_timezone(calendar_id="primary") -> str:
    """Placeholder function - OAuth not configured"""
    logger.warning("Google Calendar not configured - get_calendar_timezone disabled")
    return "UTC"


def list_calendars() -> List[Dict[str, Any]]:
    """Placeholder function - OAuth not configured"""
    logger.warning("Google Calendar not configured - list_calendars disabled")
    return []


def get_events(calendar_id="primary", time_min=None, time_max=None, max_results=10) -> List[Dict[str, Any]]:
    """Placeholder function - OAuth not configured"""
    logger.warning("Google Calendar not configured - get_events disabled")
    return []


def create_event(calendar_id="primary", event_data=None) -> Dict[str, Any]:
    """Placeholder function - OAuth not configured"""
    logger.warning("Google Calendar not configured - create_event disabled")
    return {"id": "placeholder", "status": "disabled"}


def update_event(calendar_id="primary", event_id=None, event_data=None) -> Dict[str, Any]:
    """Placeholder function - OAuth not configured"""
    logger.warning("Google Calendar not configured - update_event disabled")
    return {"id": "placeholder", "status": "disabled"}


def reschedule_event(calendar_id="primary", event_id=None, new_start=None, new_end=None) -> Dict[str, Any]:
    """Placeholder function - OAuth not configured"""
    logger.warning("Google Calendar not configured - reschedule_event disabled")
    return {"id": "placeholder", "status": "disabled"}


# Original code is preserved in scheduler.py.backup
# Uncomment and restore when Google OAuth is properly configured
logger.info("Google Calendar Scheduler temporarily disabled - OAuth not configured")
