# This file is for testing out the implemented notion api tools that the agents will use
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from datetime import datetime


from backend.notion_api import NotionAPI
from backend.models.assignment import Assignment


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

    # Test finding Assignment
    assignment = notion._find_assignment_page("HW 1")
    print("Found assignment:", assignment)

    # Test Updating Assignment Page
    # This is really important for the model to be able to update the status of an assignment
    
    assignment = Assignment(
        id=notion._find_assignment_page("HW 1")["id"] if notion._find_assignment_page("HW 1") else None,
        name="HW 1",
        due_date=datetime(2025, 10, 1),
        description="Updated description",
        course_name="Math",
        status="Not Started",
        priority="Low",
    )

    updated_page = notion._update_assignment_page(assignment)
    print("Updated page:", updated_page)


def main():
    test_notion_api()


if __name__ == "__main__":
    main()
