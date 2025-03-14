from notion_client import Client
from datetime import datetime
import pytz
from typing import Dict, Optional
from datetime import timezone
from models.assignment import Assignment
from bs4 import BeautifulSoup
import re
import logging
import backoff
from ratelimit import limits, sleep_and_retry
import dotenv
import os


dotenv.load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
COURSE_DATABASE_ID = os.environ.get("COURSE_DATABASE_ID")

logger = logging.getLogger(__name__)

# NotionAPI: Handles integration between Canvas assignments and Notion database
# Manages rate limiting, error handling, and data transformation

class NotionAPI:
    """
    Manages interaction with Notion API for syncing Canvas assignments.
    Handles rate limiting, retries, and data transformation.
    """
    
    ONE_SECOND = 1
    MAX_REQUESTS_PER_SECOND = 3

    def __init__(self):
        self.notion = Client(auth=NOTION_TOKEN)
        self.database_id = NOTION_DATABASE_ID
        self.course_db_id = COURSE_DATABASE_ID
        self.course_mapping = {}  # Initialize empty
        self.course_name_mapping = {}  # For name→id mapping
        self.last_mapping_refresh = None
        self._refresh_course_mapping()  # Load on init

    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=ONE_SECOND)
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5
    )
    def _make_notion_request(self, operation_type: str, **kwargs):
        """
        Rate-limited wrapper for Notion API calls with exponential backoff.
        
        Args:
            operation_type: Type of Notion operation ('query_database', 'update_page', 'create_page')
            **kwargs: Arguments passed to the Notion API call
        
        Returns:
            Response from Notion API
        
        Raises:
            ValueError: If operation_type is invalid
        """
        if operation_type == "query_database":
            return self.notion.databases.query(**kwargs)
        elif operation_type == "update_page":
            return self.notion.pages.update(**kwargs)
        elif operation_type == "create_page":
            return self.notion.pages.create(**kwargs)
        raise ValueError(f"Unknown operation type: {operation_type}")
    
    def _parse_date(self, date_str) -> Optional[datetime]:
        """Helper to parse dates from various formats"""
        if not date_str:
            return None
        if isinstance(date_str, datetime):
            dt = date_str
        else:
            try:
                if 'Z' in date_str:
                    date_str = date_str.replace('Z', '+00:00')
                dt = datetime.fromisoformat(date_str)
            except ValueError as e:
                logger.warning(f"Could not parse date: {date_str}. Error: {e}")
                return None

        dt = dt.astimezone(pytz.timezone('US/Eastern'))
        
        # Optional: If time is exactly 11:59, return date only (adjust as needed)
        if dt.hour == 23 and dt.minute == 59:
            return dt.date()
            
        return dt
    
    def _refresh_course_mapping(self):
        """Refresh the course mappings with timeout"""
        try:
            self.course_mapping = self._get_course_mapping()
            # Also create a name-to-id mapping for fuzzy matching
            self.course_name_mapping = self._get_course_name_mapping()
            self.last_mapping_refresh = datetime.now()
        except Exception as e:
            logger.error(f"Failed to refresh course mappings: {e}")
    
    def _get_course_name_mapping(self) -> Dict[str, str]:
        """Maps course names to Notion page UUIDs from the course database."""
        mapping = {}
        try:
            response = self._make_notion_request(
                "query_database",
                database_id=self.course_db_id,
                page_size=100
            )
            
            for page in response.get('results', []):
                try:
                    notion_uuid = page['id']
                    properties = page['properties']
                    
                    # Get the course name
                    if 'Course Name' in properties and properties['Course Name'].get('title'):
                        name = properties['Course Name']['title'][0]['text']['content']
                        mapping[name.lower()] = notion_uuid
                        # Also store common abbreviations or partial matches
                        parts = name.split(' - ')
                        if len(parts) > 1:
                            course_code = parts[0].strip()
                            mapping[course_code.lower()] = notion_uuid
                except Exception as e:
                    logger.warning(f"Error processing course page: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error building course name mapping: {e}")
        
        return mapping


    def get_course_id(self, course_name: str):
        """
        Get the Notion page UUID for a specific course name from the Notion database
        
        Args:
            course_name: The name of the course to find
            
        Returns:
            str: The Notion page UUID if found, None otherwise
        """
        try:
            response = self._make_notion_request(
                "query_database",
                database_id=self.course_db_id,
                page_size=100
            )
            
            for page in response['results']:
                try:
                    properties = page['properties']
                    name = properties['Course Name']['title'][0]['text']['content']
                    if name == course_name:
                        return page['id']  # This returns the Notion UUID
                except KeyError as e:
                    logger.error(f"Missing property in page {page.get('id')}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing page {page.get('id')}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get course UUID: {e}")
            return None
    
    def _get_course_mapping(self) -> Dict[str, str]:
        """
        Maps Canvas course IDs to Notion page UUIDs from the course database.
        
        Returns:
            Dict mapping Canvas course IDs (str) to Notion page UUIDs (str)
        """
        try:
            response = self._make_notion_request(
                "query_database",
                database_id=self.course_db_id,
                page_size=100
            )
            
            mapping = {}
            
            # Debug full response
            logger.debug(f"Full response: {response}")
            
            for page in response['results']:
                try:
                    # Get page ID and properties
                    notion_uuid = page['id']
                    properties = page['properties']
                    
                    # Debug properties
                    logger.debug(f"Page {notion_uuid} properties: {properties}")
                    
                    # Access multi-select values directly
                    canvas_ids = properties['CourseID']['multi_select']
                    logger.debug(f"Canvas IDs found: {canvas_ids}")
                    
                    # Map each selected value to this page
                    for item in canvas_ids:
                        canvas_id = item['name']  # Direct access to name
                        logger.info(f"Mapping Canvas ID {canvas_id} to page {notion_uuid}")
                        mapping[str(canvas_id)] = notion_uuid
                
                except KeyError as e:
                    logger.error(f"Missing property in page {page.get('id')}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing page {page.get('id')}: {e}")
                    continue
            
            logger.info(f"Final mappings: {mapping}")
            return mapping
            
        except Exception as e:
            logger.error(f"Failed to get course mapping: {e}")
            return {}
        
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
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:2000]  # Notion's limit
        except Exception as e:
            logger.warning(f"Error cleaning HTML content: {e}")
            return html_content[:2000]

    def get_assignment_page(self, assignment_parameter):

        """
        Retrieves existing assignment page from Notion by Canvas assignment ID or name.
        
        Args:
            assignment_parameter: Either Canvas assignment ID (int) or assignment name (str)
        
        Returns:
            Notion page object if found, None otherwise
        """
        try:
            if isinstance(assignment_parameter, int) or (isinstance(assignment_parameter, str) and assignment_parameter.isdigit()):
                # If parameter is an integer or string of digits, treat as assignment ID
                filter_condition = {
                    "property": "AssignmentID",
                    "number": {"equals": int(assignment_parameter)}
                }
            elif isinstance(assignment_parameter, str):
                # If parameter is a string, treat as assignment name
                filter_condition = {
                    "property": "Assignment Title",
                    "title": {"equals": assignment_parameter}
                }
            else:
                logger.warning(f"Invalid parameter type: {type(assignment_parameter)}")
                return None
                
            response = self._make_notion_request(
                "query_database",
                database_id=self.database_id,
                filter=filter_condition
            )
            results = response.get('results', [])
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error fetching assignment ({assignment_parameter}) from Notion: {str(e)}")
            return None
        
    def get_all_assignments(self):
        """
        Retrieves all assignments from the Notion database.
        
        Returns:
            List of all assignment pages in the Notion database
        """
        assignments = []
        next_cursor = None
        
        try:
            simplified_assignments = []
            while True:
                query_params = {
                    "database_id": self.database_id,
                    "page_size": 100 
                }
                
                if next_cursor:
                    query_params["start_cursor"] = next_cursor
                
                response = self._make_notion_request(
                    "query_database",
                    **query_params
                )
                
                # Extract only the requested fields from each assignment
                for page in response.get('results', []):
                    properties = page.get('properties', {})
                    
                    # Extract assignment title
                    title = ""
                    title_property = properties.get('Assignment Title', {}).get('title', [])
                    if title_property and len(title_property) > 0:
                        title = title_property[0].get('text', {}).get('content', "")
                    
                    # Extract due date
                    due_date = None
                    date_property = properties.get('Due Date', {}).get('date', {})
                    if date_property:
                        due_date = date_property.get('start')
                    
                    # Extract status
                    status = ""
                    status_property = properties.get('Status', {}).get('status', {})
                    if status_property:
                        status = status_property.get('name', "")
                    
                    # Extract course relation ID
                    course_id = ""
                    course_property = properties.get('Course', {}).get('relation', [])
                    if course_property and len(course_property) > 0:
                        course_id = course_property[0].get('id', "")
                    
                    # Create simplified assignment object
                    simplified_assignment = {
                        'name': title,
                        'due_date': due_date,
                        'status': status,
                        'course': course_id
                    }
                    
                    simplified_assignments.append(simplified_assignment)
                
                # Check if there are more pages
                next_cursor = response.get('next_cursor')
                if not next_cursor:
                    break
            
            return simplified_assignments
            
        except Exception as e:
            logger.error(f"Error fetching all assignments from Notion: {str(e)}")
            return []  # Return empty list on error

    def create_assignment(self, assignment: Assignment):
        """
        Create a new assignment in Notion from a Canvas assignment object.
        
        Args:
            assignment: Assignment object to create. Assignment ID is optional.
        
        Returns:
            None
        """
        try:
            # Convert course_id to string and look up UUID
            course_id_str = str(assignment.course_id)
            course_uuid = self.course_mapping.get(course_id_str)
            logger.debug(f"Looking up course {course_id_str} in mapping: {self.course_mapping}")

            if not course_uuid:
                logger.warning(f"No Notion UUID found for course {course_id_str}")
                return f"No Notion UUID found for course {course_id_str}"
            
            # Parse due date using the helper
            due_date = self._parse_date(assignment.due_date)
            
            # Prepare properties
            properties = {
                "Assignment Title": {"title": [{"text": {"content": str(assignment.name)}}]},
                "Description": {"rich_text": [{"text": {"content": self._clean_html(assignment.description)}}]},
                "Course": {"relation": [{"id": course_uuid}]},
                "Status": {"status": {"name": str(assignment.status)}},
            }
            
            # Add AssignmentID only if available
            if hasattr(assignment, 'id') and assignment.id is not None:
                properties["AssignmentID"] = {"number": int(assignment.id)}

            # Handle due date
            if due_date:
                properties["Due Date"] = {"date": {"start": due_date.isoformat()}}

            # Handle priority
            VALID_PRIORITIES = ["Low", "Medium", "High"]
            if hasattr(assignment, 'priority') and assignment.priority in VALID_PRIORITIES:
                properties["Priority"] = {"select": {"name": assignment.priority}}
            else:
                properties["Priority"] = {"select": {"name": "Low"}}  # Default to Low
                
            # Handle assignment group if available
            if hasattr(assignment, 'group_name') and assignment.group_name:
                properties["Assignment Group"] = {"select": {"name": assignment.group_name}}
                
            # Handle group weight if available
            if hasattr(assignment, 'group_weight') and assignment.group_weight is not None:
                properties["Group Weight"] = {"number": assignment.group_weight}

            # Remove None values
            properties = {k: v for k, v in properties.items() if v is not None}
            
            # Handle grade
            if hasattr(assignment, 'grade') and assignment.grade is not None:
                try:
                    properties["Grade (%)"] = {"number": float(assignment.grade)}
                except (ValueError, TypeError):
                    logger.warning(f"Invalid grade format for assignment {assignment.name}: {assignment.grade}")
                    if hasattr(assignment, "mark") and assignment.mark is not None:
                        try:
                            properties["Status"] = {"status": {"name": "Mark received"}}
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid mark format for assignment {assignment.name}: {assignment.mark}")

            logger.info(f"Creating new assignment: {assignment.name}")
            self._make_notion_request(
                "create_page",
                parent={"database_id": self.database_id},
                properties=properties
            )
        except Exception as e:
            logger.error(f"Error creating assignment {assignment.name} in Notion: {str(e)}")
            raise

    def update_assignment(self, update_data: Dict):
        """
        Update specific fields of an existing assignment in Notion.
        
        Args:
            update_data: Dictionary containing fields to update. 
                         Must contain either 'id' or 'name' to identify the assignment.
        
        Returns:
            None if successful, error message if failed
        """
        try:
            # Check if we have an identifier to find the assignment
            if 'id' not in update_data and 'name' not in update_data:
                logger.error("Update data must contain either 'id' or 'name' to identify the assignment")
                return "Update data must contain either 'id' or 'name' to identify the assignment"
                
            # Get existing page
            existing_page = None
            if 'id' in update_data:
                existing_page = self.get_assignment_page(update_data['id'])
            
            if existing_page is None and 'name' in update_data:
                existing_page = self.get_assignment_page(update_data['name'])
                
            if existing_page is None:
                identifier = update_data.get('id') or update_data.get('name')
                logger.warning(f"No existing page found for assignment {identifier}")
                return f"No existing page found for assignment {identifier}"
            
            # Initialize properties dictionary - we'll only add what's in update_data
            properties = {}
            
            # Handle name/title update
            if 'name' in update_data:
                properties["Assignment Title"] = {"title": [{"text": {"content": str(update_data['name'])}}]}
            
            # Handle description update
            if 'description' in update_data:
                properties["Description"] = {"rich_text": [{"text": {"content": self._clean_html(update_data['description'])}}]}
            
            # Handle course update
            if 'course_id' in update_data:
                course_id_str = str(update_data['course_id'])
                course_uuid = self.course_mapping.get(course_id_str)
                if not course_uuid:
                    logger.warning(f"No Notion UUID found for course {course_id_str}")
                    return f"No Notion UUID found for course {course_id_str}"
                properties["Course"] = {"relation": [{"id": course_uuid}]}
            
            # Handle status update
            if 'status' in update_data:
                properties["Status"] = {"status": {"name": str(update_data['status'])}}
            
            # Handle due date update
            if 'due_date' in update_data:
                due_date = self._parse_date(update_data['due_date'])
                if due_date:
                    properties["Due Date"] = {"date": {"start": due_date.isoformat()}}
            
            # Handle assignment group update
            if 'group_name' in update_data and update_data['group_name']:
                properties["Assignment Group"] = {"select": {"name": update_data['group_name']}}
            
            # Handle group weight update
            if 'group_weight' in update_data and update_data['group_weight'] is not None:
                properties["Group Weight"] = {"number": update_data['group_weight']}
            
            # Handle priority update
            if 'priority' in update_data:
                VALID_PRIORITIES = ["Low", "Medium", "High"]
                priority = update_data['priority']
                if priority in VALID_PRIORITIES:
                    properties["Priority"] = {"select": {"name": priority}}
                else:
                    properties["Priority"] = {"select": {"name": "Low"}}  # Default to Low
            
            # Handle grade update
            if 'grade' in update_data and update_data['grade'] is not None:
                try:
                    properties["Grade (%)"] = {"number": float(update_data['grade'])}
                    # Only set status to "Mark received" if we're updating the grade and not already setting status
                    if 'status' not in update_data:
                        properties["Status"] = {"status": {"name": "Mark received"}}
                except (ValueError, TypeError):
                    logger.warning(f"Invalid grade format: {update_data['grade']}")
            
            # Check if we have anything to update
            if not properties:
                logger.info("No properties to update")
                return "No properties to update"
            
            # Check current status for special cases
            current_status = existing_page["properties"]["Status"]["status"]["name"]
            if current_status == "Dont show" and 'status' not in update_data:
                logger.info(f"Skipping update due to 'Dont show' status")
                return "Skipping update due to 'Dont show' status"
            elif current_status == "In progress" and 'status' not in update_data:
                # Don't change the status if it's currently "In progress" unless explicitly requested
                properties.pop("Status", None)
            
            logger.info(f"Updating assignment fields: {', '.join(properties.keys())}")
            self._make_notion_request(
                "update_page",
                page_id=existing_page["id"],
                properties=properties
            )
            return None
        except Exception as e:
            identifier = update_data.get('id') or update_data.get('name', 'Unknown')
            logger.error(f"Error updating assignment {identifier} in Notion: {str(e)}")
            raise
