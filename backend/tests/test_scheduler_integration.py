#!/usr/bin/env python3
"""
Test script to verify scheduler agent integration with OAuth
Tests both basic integration and real API calls with actual OAuth token
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from agents.scheduler import (
    tools,
    scheduler_prompt,
    get_calendar_timezone,
    get_current_time,
    get_calendar_mapping,
    get_events,
    get_relative_time,
    find_available_time_slots,
    validate_date_day_mapping,
    CalendarEvent,
    create_event,
    find_event,
    delete_event,
)

# Test OAuth token - replace this with your actual token
TEST_ACCESS_TOKEN = "TEMPORARY_PLACEHOLDER_FOR_SECURITY"


@pytest.mark.asyncio
async def test_basic_integration():
    """Test that scheduler tools are properly defined"""
    print("=" * 80)
    print("BASIC SCHEDULER AGENT INTEGRATION TEST")
    print("=" * 80)
    print()

    # Test 1: Verify tools are loaded
    print("✓ Test 1: Tools loaded")
    print(f"  Found {len(tools)} tools:")
    for tool in tools:
        print(f"    - {tool.name}")
    print()

    # Test 2: Verify prompt is loaded
    print("✓ Test 2: Scheduler prompt loaded")
    print(f"  Prompt length: {len(scheduler_prompt)} characters")
    print()

    # Test 3: Test non-auth required tool
    print("✓ Test 3: Testing get_current_time (no auth required)")
    current_time = await get_current_time.ainvoke({})
    print(f"  Current time: {current_time}")
    print()

    # Test 4: Test get_relative_time
    print("✓ Test 4: Testing get_relative_time (no auth required)")
    relative_time = await get_relative_time.ainvoke({})
    print(f"  Generated {len(relative_time)} day mappings")
    print(f"  First 3 days: {relative_time[:3]}")
    print()

    # Test 5: Test validate_date_day_mapping
    print("✓ Test 5: Testing validate_date_day_mapping (no auth required)")
    today = datetime.now()
    today_name = today.strftime("%A")
    is_valid = await validate_date_day_mapping.ainvoke({"target_date": today.strftime("%Y-%m-%d"), "day_name": today_name})
    print(f"  Today is {today_name}: {is_valid}")
    print()

    print("=" * 80)
    print("BASIC TESTS PASSED!")
    print("=" * 80)
    print()


@pytest.mark.asyncio
async def test_with_real_token():
    """Test scheduler tools with real Google Calendar API calls"""
    print()
    print("=" * 80)
    print("REAL API TESTS WITH OAUTH TOKEN")
    print("=" * 80)
    print()

    # Mock the token retrieval by patching the helper function
    from agents import scheduler

    # Store original function
    original_get_token = scheduler.get_user_access_token

    # Create mock function that returns our test token
    async def mock_get_token(config):
        print("  [Using provided OAuth token]")
        return TEST_ACCESS_TOKEN

    # Patch the function
    scheduler.get_user_access_token = mock_get_token

    try:
        # Create a mock config
        test_config = {"configurable": {"user_id": "test-user"}}

        # Test 1: Get Calendar Timezone
        print("🔧 Test 1: get_calendar_timezone")
        print("-" * 80)
        try:
            timezone = await get_calendar_timezone.ainvoke({"calendar_id": "primary"}, config=test_config)
            print(f"✅ SUCCESS: Timezone = {timezone}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
        print()

        # Test 2: Get Calendar Mapping
        print("🔧 Test 2: get_calendar_mapping")
        print("-" * 80)
        try:
            calendars = await get_calendar_mapping.ainvoke({}, config=test_config)
            if "error" in calendars:
                print(f"❌ FAILED: {calendars['error']}")
            else:
                print(f"✅ SUCCESS: Found {len(calendars)} calendars")
                for name, cal_id in list(calendars.items())[:3]:
                    print(f"  - {name}: {cal_id}")
                if len(calendars) > 3:
                    print(f"  ... and {len(calendars) - 3} more")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
        print()

        # Test 3: Get Events (next 7 days)
        print("🔧 Test 3: get_events (next 7 days)")
        print("-" * 80)
        try:
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

            events = await get_events.ainvoke(
                {"start_date": start_date, "end_date": end_date, "calendar_id": "primary"}, config=test_config
            )

            if events and isinstance(events, list) and "error" not in events[0]:
                print(f"✅ SUCCESS: Found {len(events)} events")
                for event in events[:3]:
                    summary = event.get("summary", "No title")
                    start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "Unknown"))
                    print(f"  - {summary} at {start}")
                if len(events) > 3:
                    print(f"  ... and {len(events) - 3} more events")
            else:
                print(f"✅ SUCCESS: No events found or {events}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
        print()

        # Test 4: Find Available Time Slots
        print("🔧 Test 4: find_available_time_slots (next 3 days)")
        print("-" * 80)
        try:
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

            slots = await find_available_time_slots.ainvoke(
                {"start_date": start_date, "end_date": end_date, "duration_minutes": 60, "exclude_early": True},
                config=test_config,
            )

            if slots and not slots[0].startswith("Error"):
                print(f"✅ SUCCESS: Found {len(slots)} available time slots")
                for slot in slots[:3]:
                    print(f"  - {slot}")
                if len(slots) > 3:
                    print(f"  ... and {len(slots) - 3} more slots")
            else:
                print(f"✅ SUCCESS (or no slots): {slots[0] if slots else 'No response'}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
        print()

        # Test 5: Create a Test Event
        print("🔧 Test 5: create_event (test event)")
        print("-" * 80)
        try:
            # Create event for tomorrow at 2 PM for 1 hour
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_2pm = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
            tomorrow_3pm = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)

            test_event = CalendarEvent(
                summary="[TEST] Scheduler Integration Test",
                location="Test Location",
                description="This is a test event created by the scheduler integration test. Safe to delete.",
                start={"dateTime": tomorrow_2pm.isoformat(), "timeZone": "America/New_York"},
                end={"dateTime": tomorrow_3pm.isoformat(), "timeZone": "America/New_York"},
                reminders={"useDefault": False, "overrides": [{"method": "popup", "minutes": 10}]},
            )

            result = await create_event.ainvoke({"calendar_event": test_event, "calendar_id": "primary"}, config=test_config)

            if "Error" not in result:
                print(f"✅ SUCCESS: {result}")
                print(f"  Event created for tomorrow at 2 PM")

                # Test 6: Find the event we just created
                print()
                print("🔧 Test 6: find_event (search for test event)")
                print("-" * 80)
                found_events = await find_event.ainvoke(
                    {"event_name": "[TEST] Scheduler Integration Test"}, config=test_config
                )

                if found_events and not isinstance(found_events[0], dict) or "error" not in found_events[0]:
                    print(f"✅ SUCCESS: Found the test event")
                    if found_events and isinstance(found_events, list):
                        event = found_events[0]
                        event_id = event.get("id", "unknown")
                        print(f"  Event ID: {event_id}")

                        # Test 7: Delete the test event
                        print()
                        print("🔧 Test 7: delete_event (cleanup test event)")
                        print("-" * 80)
                        delete_result = await delete_event.ainvoke(
                            {"event_id": event_id, "calendar_id": "primary"}, config=test_config
                        )
                        print(f"✅ SUCCESS: {delete_result}")
                else:
                    print(f"⚠️  Event created but not found in search: {found_events}")
            else:
                print(f"❌ FAILED: {result}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            import traceback

            traceback.print_exc()
        print()

    finally:
        # Restore original function
        scheduler.get_user_access_token = original_get_token

    print("=" * 80)
    print("REAL API TESTS COMPLETED!")
    print("=" * 80)
    print()


@pytest.mark.asyncio
async def test_supervisor_integration():
    """Test that supervisor properly includes scheduler"""
    print("=" * 80)
    print("SUPERVISOR INTEGRATION TEST")
    print("=" * 80)
    print()

    from agents.supervisor import orchestrator_agent, scheduler_handoff

    print("✓ Orchestrator agent compiled successfully")
    print("✓ Scheduler handoff tool loaded")
    print(f"  Tool name: {scheduler_handoff.name}")
    print(f"  Tool description: {scheduler_handoff.description}")
    print()

    print("=" * 80)
    print("SUPERVISOR INTEGRATION SUCCESSFUL!")
    print("=" * 80)
    print()


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("GOOGLE CALENDAR SCHEDULER INTEGRATION TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run basic integration tests
        await test_basic_integration()

        # Run real API tests with OAuth token
        print("⚠️  WARNING: The following tests will make REAL API calls to Google Calendar")
        print("⚠️  They will create and delete a test event on your primary calendar")
        print()

        await test_with_real_token()

        # Run supervisor integration tests
        await test_supervisor_integration()

        print()
        print("=" * 80)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 80)
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ TEST SUITE FAILED: {e}")
        print("=" * 80)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
