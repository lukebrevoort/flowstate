# This file is for testing out the implemented notion api tools that the agents will use
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from datetime import datetime


from backend.notion_api import NotionAPI
from backend.models.assignment import Assignment


def test_multiple_assignment_updates():
    """Test the multiple assignment update functionality specifically"""
    print("\n" + "=" * 50)
    print("TESTING MULTIPLE ASSIGNMENT UPDATES")
    print("=" * 50)

    notion = NotionAPI(user_id="99d11141-76eb-460f-8741-f2f5e767ba0f")

    # Create test assignments
    assignments = {
        "Math Assignment 1": Assignment(
            name="Math Assignment 1",
            due_date=datetime(2025, 11, 1),
            description="Updated math homework",
            course_name="Math",
            status="In progress",
            priority="High",
        ),
        "Math Assignment 2": Assignment(
            name="Math Assignment 2",
            due_date=datetime(2025, 11, 15),
            description="Advanced calculus problems",
            course_name="Math",
            status="Not started",
            priority="Medium",
        ),
        "Physics Lab": Assignment(
            name="Physics Lab",
            due_date=datetime(2025, 10, 30),
            description="Laboratory report on momentum",
            course_name="Physics",
            status="Submitted",
            priority="Low",
        ),
    }

    print(f"Attempting to update {len(assignments)} assignments:")
    for name, assignment in assignments.items():
        print(f"  - {name}: {assignment.status} (Priority: {assignment.priority})")

    # Perform batch update
    results = notion.update_assignment_page(updates=assignments)

    print("\nUpdate Results:")
    if results:
        for assignment_name, result in results.items():
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            print(f"  {assignment_name}: {status}")
            if not result["success"] and result["error"]:
                print(f"    Error: {result['error']}")
    else:
        print("  No results returned")

    return results


def test_notion_api():
    notion = NotionAPI(user_id="99d11141-76eb-460f-8741-f2f5e767ba0f")

    token_info = notion.get_token_info()
    print("Token info:", token_info)

    # Check data source info
    data_source_info = notion.get_data_source_info()
    print("Data source info:", data_source_info)

    # Get data source schema if available
    if data_source_info["using_data_source"]:
        schema = notion.get_data_source_schema()
        if schema and "properties" in schema:
            print("Data source properties:")
            for name, prop in schema["properties"].items():
                print(f"  {name}: {prop['type']}")

    # Test multiple assignment updates
    assignment1 = Assignment(
        name="HW 1",
        due_date=datetime(2025, 11, 1),
        description="Updated description for HW 1",
        course_name="Math",
        status="In progress",
        priority="High",
    )

    assignment2 = Assignment(
        name="HW 2",
        due_date=datetime(2025, 12, 1),
        description="This Crazy and new and quirky description",
        course_name="Math",
        status="Not started",
        priority="Medium",
    )

    # Correct format: string keys mapping to Assignment objects
    assignments_dict = {"HW 1": assignment1, "HW 2": assignment2}

    # Use the updates parameter correctly
    results = notion.update_assignment_page(updates=assignments_dict)
    print("Update results:", results)


def main():
    # Run basic API test
    test_notion_api()

    # Run focused multiple updates test
    test_multiple_assignment_updates()


def main():
    test_notion_api()


if __name__ == "__main__":
    main()
