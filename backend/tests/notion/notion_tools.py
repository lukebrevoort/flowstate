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
    assignments = retrieve_assignments.invoke({"config": config, "filters": {"status": "Not started"}})
    print("Assignments:", assignments)


if __name__ == "__main__":
    main()
