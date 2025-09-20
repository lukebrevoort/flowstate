#!/usr/bin/env python
# filepath: /Users/lbrevoort/Desktop/flowstate/backend/verify_calendar_auth.py
"""
Utility script to verify Google Calendar authentication is working correctly.
This script attempts to connect to Google Calendar and list upcoming events.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def verify_calendar_auth():
    """Verify that calendar authentication is working"""
    try:
        # Import the calendar service getter
        from utils.calendar_auth import get_calendar_service

        logger.info("Attempting to get calendar service...")
        service = get_calendar_service()
        logger.info("Successfully connected to Google Calendar API")

        # Try to list some events as a test
        logger.info("Attempting to list calendar events...")
        now = datetime.utcnow()
        end = now + timedelta(days=7)  # Look one week ahead

        # Call the Calendar API
        events_result = (
            service.events()
            .list(
                calendarId="primary",  # Use 'primary' for the user's primary calendar
                timeMin=now.isoformat() + "Z",  # 'Z' indicates UTC time
                timeMax=end.isoformat() + "Z",
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found in the next 7 days.")
        else:
            print("Upcoming events (next 7 days):")
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(f"{start}: {event['summary']}")

        logger.info("Calendar authentication verification completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error verifying calendar authentication: {str(e)}")
        print(f"ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("Verifying Google Calendar authentication...")
    success = verify_calendar_auth()
    sys.exit(0 if success else 1)
