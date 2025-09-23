# This page is responsible for interacting with the Notion API to manage
# and pull assignments from the Notion Database.
# It includes rate limiting, error handling, and data transformation.
# All about making the Notion API work smoothly with our application and our PM agent super simple.

from notion_client import Client
from datetime import datetime
import pytz
from typing import Dict, Optional, Any
from datetime import timezone

try:
    # Try relative import (for CI/normal backend execution)
    from models.assignment import Assignment
except ImportError:
    # Fall back to absolute import (for test scripts run from project root)
    from backend.models.assignment import Assignment
from bs4 import BeautifulSoup
import re
import logging
import backoff
from ratelimit import limits, sleep_and_retry
import dotenv
import os
import requests


dotenv.load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
# Course database is now a data source for course pages and in the same database assignments.

logger = logging.getLogger(__name__)

# NotionAPI: Handles integration between Canvas assignments and Notion database
# Manages rate limiting, error handling, and data transformation


class NotionAPI:
    """
    Manages interaction with Notion API for syncing Canvas assignments.
    Handles rate limiting, retries, and data transformation.
    Now supports user-specific tokens from OAuth.
    """

    ONE_SECOND = 1
    MAX_REQUESTS_PER_SECOND = 3

    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize NotionAPI with optional user-specific token

        Args:
            user_id: Optional user ID to fetch user-specific Notion token
        """
        self.user_id = "99d11141-76eb-460f-8741-f2f5e767ba0f"  # or user.id  # Default system user ID for testing purposes
        self.user_token = None
        self.data_source_id = None  # Store the data source ID for this database
        self.database_id = None  # Initialize database ID for OAuth users

        # If user_id is provided, try to get their token
        if user_id:
            self.user_token = self._get_user_token(user_id)
            if self.user_token:
                logger.info(f"Using OAuth token for user {user_id}")
            else:
                logger.info(f"No OAuth token found for user {user_id}, falling back to system token")
        else:
            logger.info("No user_id provided, using system token")

        # Use user token if available, otherwise fall back to system token

        token = self.user_token or NOTION_TOKEN  # pulled from testing user
        if not token:
            raise ValueError("No Notion token available (neither user token nor system token)")

        self.notion = Client(auth=token, notion_version="2025-09-03")

        self.database_id = self._get_database_id() or NOTION_DATABASE_ID
        # Initialize data source ID
        self._initialize_data_source()

    def _get_user_token(self, user_id: str) -> Optional[str]:
        """
        Get user's Notion token from database using UserTokenService

        Args:
            user_id: User ID

        Returns:
            User's Notion access token if available
        """
        try:
            try:
                # Try relative import (for CI/normal backend execution)
                from services.user_tokens import UserTokenService
            except ImportError:
                # Fall back to absolute import (for test scripts run from project root)
                from backend.services.user_tokens import UserTokenService
            import asyncio

            async def fetch_token():
                return await UserTokenService.get_user_notion_token(user_id)

            # Run async function in sync context
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(fetch_token())
            except RuntimeError:
                # No event loop running, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(fetch_token())
                finally:
                    loop.close()

        except Exception as e:
            logger.warning(f"Could not fetch user token for {user_id}: {e}")
            return None

    def _get_database_id(self) -> Optional[str]:
        """
        Get the Notion database ID, either from environment or by querying Notion.

        Returns:
            Database ID if found, else None
        """
        try:
            # Search for databases using the correct filter syntax for 2025-09-03 API
            response = self.notion.search(
                filter={
                    "value": "data_source",  # Changed from "database" to "data_source" for new API
                    "property": "object",
                }
            )
            if response and "results" in response and len(response["results"]) > 0:
                # Get the parent database ID from the first data source found
                first_result = response["results"][0]
                if "parent" in first_result and first_result["parent"]["type"] == "database_id":
                    db_id = first_result["parent"]["database_id"]
                    logger.info(f"Found Notion database ID: {db_id}")
                    return db_id
                else:
                    logger.warning("No parent database found in search results")
                    return NOTION_DATABASE_ID
            else:
                logger.warning("No data sources found in Notion workspace")
                return NOTION_DATABASE_ID
        except Exception as e:
            logger.error(f"Error fetching Notion databases, using system ID: {e}")
            return NOTION_DATABASE_ID

    def _initialize_data_source(self) -> None:
        """
        Initialize data source IDs by fetching from the database.
        This handles multiple data sources (Assignments and Courses).
        This implements Step 1 from the 2025-09-03 upgrade guide.
        """
        self.assignments_data_source_id = None
        self.courses_data_source_id = None

        try:
            if not self.database_id:
                logger.warning("No database_id configured")
                return

            # Get database info to retrieve data sources
            response = self.notion.databases.retrieve(database_id=self.database_id)

            if response and "data_sources" in response:
                data_sources = response["data_sources"]
                logger.info(f"Found {len(data_sources)} data sources")

                for data_source in data_sources:
                    data_source_id = data_source["id"]
                    data_source_name = data_source.get("name", "").lower()

                    logger.info(f"Data source: {data_source_name} (ID: {data_source_id})")

                    # Identify data sources by name
                    if "assignment" in data_source_name:
                        self.assignments_data_source_id = data_source_id
                        logger.info(f"Assignments data source: {data_source_id}")
                    elif "course" in data_source_name:
                        self.courses_data_source_id = data_source_id
                        logger.info(f"Courses data source: {data_source_id}")

                # Set the primary data_source_id to assignments for backward compatibility
                self.data_source_id = self.assignments_data_source_id

                if not self.assignments_data_source_id:
                    logger.warning("No assignments data source found")
                if not self.courses_data_source_id:
                    logger.warning("No courses data source found")

            else:
                logger.warning("No data_sources field in database response")

        except Exception as e:
            logger.error(f"Failed to initialize data sources: {e}")
            # Fall back to using database_id if data source discovery fails
            self.data_source_id = None
            self.assignments_data_source_id = None
            self.courses_data_source_id = None

    def get_data_source_info(self) -> Dict[str, Any]:
        """
        Get information about the current data sources being used

        Returns:
            Dictionary with data source information
        """
        return {
            "database_id": self.database_id,
            "assignments_data_source_id": self.assignments_data_source_id,
            "courses_data_source_id": self.courses_data_source_id,
            "primary_data_source_id": self.data_source_id,
            "using_data_source": self.data_source_id is not None,
            "has_both_data_sources": bool(self.assignments_data_source_id and self.courses_data_source_id),
        }

    def get_data_source_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the schema (properties) of the current data source.
        This helps debug what properties are available.

        Returns:
            Data source schema information or None if unavailable
        """
        if not self.data_source_id:
            logger.warning("No data source ID available")
            return None

        try:
            response = self._make_notion_request("retrieve_data_source", data_source_id=self.data_source_id)
            return response
        except Exception as e:
            logger.error(f"Failed to retrieve data source schema: {e}")
            return None

    @property
    def is_using_user_token(self) -> bool:
        """Check if currently using user-specific token"""
        return self.user_token is not None

    def refresh_user_token(self) -> bool:
        """
        Refresh the user token from database

        Returns:
            True if token was refreshed successfully, False otherwise
        """
        if not self.user_id:
            return False

        new_token = self._get_user_token(self.user_id)
        if new_token and new_token != self.user_token:
            self.user_token = new_token
            # Reinitialize Notion client with new token
            token = self.user_token or NOTION_TOKEN
            if token:
                self.notion = Client(auth=token, notion_version="2024-05-16")
                logger.info(f"Refreshed Notion token for user {self.user_id}")
                return True
        return False

    def validate_token(self) -> bool:
        """
        Validate that the current token works by making a test API call

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Make a simple API call to test the token
            self.notion.users.me()
            return True
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return False

    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token being used

        Returns:
            Dictionary with token information
        """
        return {
            "user_id": self.user_id,
            "using_user_token": self.is_using_user_token,
            "token_valid": (self.validate_token() if self.user_token or NOTION_TOKEN else False),
            "has_system_fallback": bool(NOTION_TOKEN),
        }

    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=ONE_SECOND)
    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def _make_notion_request(self, operation_type: str, **kwargs):
        """
        Rate-limited wrapper for Notion API calls with exponential backoff.
        Supports both legacy database operations and new data source operations.

        Args:
            operation_type: Type of Notion operation ('query_database', 'query_data_source', 'update_page', 'create_page', etc.)
            **kwargs: Arguments passed to the Notion API call

        Returns:
            Response from Notion API

        Raises:
            ValueError: If operation_type is invalid
        """
        if operation_type == "query_database":
            return self.notion.databases.query(**kwargs)
        elif operation_type == "query_data_source":
            # Use the correct data source query endpoint
            data_source_id = kwargs.pop("data_source_id")
            filter_obj = kwargs.pop("filter", {})
            return self.notion.request(
                method="POST",
                path=f"data_sources/{data_source_id}/query",
                body={"filter": filter_obj},
            )
        elif operation_type == "retrieve_data_source":
            # Retrieve data source schema/properties
            data_source_id = kwargs.pop("data_source_id")
            return self.notion.request(method="GET", path=f"data_sources/{data_source_id}")
        elif operation_type == "update_page":
            return self.notion.pages.update(**kwargs)
        elif operation_type == "create_page":
            return self.notion.pages.create(**kwargs)
        elif operation_type == "blocks/children/list":
            return self.notion.blocks.children.list(**kwargs)
        elif operation_type == "blocks/children/append":
            return self.notion.blocks.children.append(**kwargs)
        raise ValueError(f"Unknown operation type: {operation_type}")

    def _parse_date(self, date_str) -> Optional[datetime]:
        """Helper to parse dates from various formats"""
        if not date_str:
            return None
        if isinstance(date_str, datetime):
            dt = date_str
        else:
            try:
                if "Z" in date_str:
                    date_str = date_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(date_str)
            except ValueError as e:
                logger.warning(f"Could not parse date: {date_str}. Error: {e}")
                return None

        # Optional: If time is exactly 11:59, return date only (adjust as needed)
        if dt.hour == 23 and dt.minute == 59:
            return dt.date()

        return dt

    def _clean_html(self, html_content: str) -> str:
        """
        Converts HTML content to plain text and truncates to Notion's 2000 char limit.

        Args:
            html_content: HTML string to clean

        Returns:
            Cleaned and truncated plain text
        """
        if not html_content:
            return ""
        try:
            # Parse HTML and get text
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text()

            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()

            return text[:2000]  # Notion's limit
        except Exception as e:
            logger.warning(f"Error cleaning HTML content: {e}")
            return html_content[:2000]

    def _get_assignment_page(self, assignment: Assignment) -> Optional[Dict[str, Any]]:
        """
        Check if a Notion page already exists for the given assignment.

        Args:
            assignment: Assignment object
        Returns:
            Notion page dict if found, else None
        """
        payload = {
            "filter": {
                "property": "Assignment Name",
                "rich_text": {"contains": assignment.name},
            }
        }

        try:
            response = self._make_notion_request("databases/query", **payload)
            if response and "results" in response:
                for page in response["results"]:
                    if page["properties"]["Assignment Name"]["rich_text"][0]["text"]["content"] == assignment.name:
                        return page
        except Exception as e:
            logger.error(f"Error fetching assignment page: {e}")
        return None

    def _get_all_assignment_pages_by_course(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all assignment pages from the Notion database grouped by course.

        Returns:
            Dictionary mapping course names to their assignment page dicts
        """
        # TODO: Implement course retrieval logic
        pass

    def _create_assignment_page(self, assignment: Assignment) -> Optional[Dict[str, Any]]:
        """
        Create a new Notion page for the given assignment.

        Args:
            assignment: Assignment object

        Returns:
            Notion page dict if created successfully, else None
        """

        course_id = self._get_course_page(assignment.course_name)["id"] if assignment.course_name else None
        properties = {
            "Assignment Name": {"title": [{"text": {"content": assignment.name}}]},
            "Status": {"status": {"name": assignment.status or "Not started"}},
            "Due date": {"date": {"start": (assignment.due_date.strftime("%Y-%m-%d") if assignment.due_date else None)}},
            "Priority": {"select": {"name": assignment.priority or "Low"}},
            "Description": {"rich_text": [{"text": {"content": self._clean_html(assignment.description)}}]},
            "Course": {"relation": [{"id": course_id} if course_id else {}]},
        }

        # Use assignments data_source_id if available (new 2025-09-03 API), fallback to database_id
        if self.assignments_data_source_id:
            payload = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": self.assignments_data_source_id,
                },
                "properties": properties,
            }
        else:
            # Fallback for older API or when data source discovery fails
            payload = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
            }

        try:
            response = self._make_notion_request("create_page", **payload)
            return response
        except Exception as e:
            logger.error(f"Error creating assignment page: {e}")
            return None

    def _find_or_create_course_page(self, course_name: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing Notion page for the course, or create one if it doesn't exist.

        Args:
            course_name: Name of the course
        Returns:
            Notion page dict if found or created, else None
        """

        course_page = self._get_course_page(course_name)
        if course_page:
            return course_page
        return self._create_course_page(course_name)
    
    def _find_assignment_page(self, assignment_name: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing Notion page for the given assignment.

        Args:
            assignment: Assignment object
        Returns:
            Notion page dict if found, else None
        """
        payload = {
            "filter": {
                "property": "Assignment Name",
                "title": {"contains": assignment_name},
            }
        }

        try:
            response = self._make_notion_request("query_data_source", data_source_id=self.assignments_data_source_id, **payload)
            if response and "results" in response:
                for page in response["results"]:
                    if page["properties"]["Assignment Name"]["title"][0]["text"]["content"] == assignment_name:
                        return page
        except Exception as e:
            logger.error(f"Error fetching assignment page: {e}")
        return None

    def _update_assignment_page(self, assignment: Assignment) -> Optional[Dict[str, Any]]:
        """
        Update an existing Notion page with new assignment data.

        Args:
            page_id: Notion page ID to update
            assignment: Assignment object with updated data

        Returns:
            Updated Notion page dict if successful, else None
        """
        cur_assignment = self._find_assignment_page(assignment.name)
        if not cur_assignment:
            logger.warning(f"No existing page found for assignment {assignment.name}")
            return None
        page_id = assignment.id or cur_assignment["id"]

        payload = {
            "id": page_id,
            "properties": {
                "Assignment Name": {"title": [{"text": {"content": assignment.name}}]},
                "Status": {"status": {"name": assignment.status or cur_assignment["properties"].get("Status", {}).get("status", {}).get("name", "Not started")}},
                "Due date": {"date": {"start": (assignment.due_date.strftime("%Y-%m-%d") if assignment.due_date else None)}},
                "Priority": {"select": {"name": assignment.priority or cur_assignment["properties"].get("Priority", {}).get("select", {}).get("name", "Low")}},
                "Description": {"rich_text": [{"text": {"content": self._clean_html(assignment.description)}}]},
                # Course relation is not updated here to avoid overwriting existing relations!
            }
        }

        try:
            response = self._make_notion_request("update_page", page_id=page_id, properties=payload["properties"])
            return response
        except Exception as e:
            logger.error(f"Error updating assignment page: {e}")
            return None
            


    def _get_course_page(self, course_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a Notion page for the given course name in the courses data source.

        Args:
            course_name: Name of the course

        Returns:
            Notion page dict if found, else None
        """

        if self.courses_data_source_id:
            # Query the courses data source for course pages
            payload = {
                "filter": {
                    "property": "Course Name",  # Assuming courses have a "Course Name" title property
                    "title": {"equals": course_name},
                }
            }
            try:
                response = self._make_notion_request(
                    "query_data_source",
                    data_source_id=self.courses_data_source_id,
                    **payload,
                )
                if response and "results" in response and len(response["results"]) > 0:
                    return response["results"][0]  # Return the first matching course
            except Exception as e:
                logger.error(f"Error fetching course page for {course_name} from courses data source: {e}")
        else:
            logger.warning("No courses data source available")
        return None

    def _create_course_page(self, course_name: str) -> Optional[Dict[str, Any]]:
        """
        Create a new Notion page for the given course.

        Args:
            course_name: Name of the course

        Returns:
            Notion page dict if created successfully, else None
        """
        # IMPLEMENT LATER

    def _get_all_course_pages(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all course pages from the Notion course database.

        Returns:
            Dictionary mapping course names to their Notion page dicts
        """
        # IMPLEMENT LATER
