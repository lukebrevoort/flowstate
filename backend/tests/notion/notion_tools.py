# This file is for testing out the implemented notion api tools that the agents will use
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from datetime import datetime


from notion_api import NotionAPI
from models.assignment import Assignment


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

    # Test creating page
    page = notion._create_assignment_page(
        Assignment(
            id=2,
            name="HW 2",
            due_date=datetime(2025, 9, 22),
            description="Math homework",
            priority="High",
            course_name="Math",
        )
    )
    print("Created page", page)

    # Test getting Course Page
    course_page = notion._get_course_page("Math")
    print("Course page:", course_page)


def main():
    test_notion_api()


if __name__ == "__main__":
    main()
