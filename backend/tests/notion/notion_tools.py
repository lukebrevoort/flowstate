# This file is for testing out the implemented notion api tools that the agents will use
import sys
import os

from dataclasses_json import config

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from datetime import datetime
from backend.agents.project_manager import (
    retrieve_assignment,
    retrieve_assignments,
    create_assignment,
)

from backend.notion_api import NotionAPI
from backend.models.assignment import Assignment


def main():
    # test the tools here

    config = {"configurable": {"user_id": "99d11141-76eb-460f-8741-f2f5e767ba0f"}}

    # Example: Retrieve assignments
    assignments = retrieve_assignments.invoke({"config": config, "filters": {"name": "HW"}})
    print("Assignments:", assignments)

    # Example: Retrieve a specific assignment
    assignment = retrieve_assignment.invoke({"assignment_name": "HW 1", "config": config})
    print("Assignment:", assignment)

    # Example: Create a new assignment
    new_assignment_dict = {
        "name": "Test Assignment",
        "course_name": "Math",
        "description": "Test description",
        "priority": "Low",
        "due_date": "2025-12-15",
    }
    created_assignment = create_assignment.invoke({"assignment": new_assignment_dict, "config": config})
    print("Created Assignment:", created_assignment)


if __name__ == "__main__":
    main()
