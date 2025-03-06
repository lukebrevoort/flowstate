import os, sys
# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.notion_api import NotionAPI


def get_course_id(course_name: str):
    """
    Get all course IDs from Notion database

    returns a list of course IDs
    """
    notion_api = NotionAPI()
    course_id = notion_api.get_course_id(course_name)
    course_id_dict = notion_api._get_course_mapping()

    for key, value in course_id_dict.items():
        if value == course_id:
            return key


print(get_course_id("PEP 112 - Electricity and Magnetism"))