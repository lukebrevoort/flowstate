from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import pickle
import logging

logger = logging.getLogger(__name__)

# Specify the scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    """
    Handles OAuth authentication and returns an authorized Google Calendar service.
    Manages token creation, storage, and refresh.
    """
    creds = None
    token_path = "/etc/secrets/token.json"

    # Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            try:
                creds = pickle.load(token)
                logger.info("Loaded existing credentials from token file")
            except Exception as e:
                logger.error(f"Error loading token: {str(e)}")

    # Refresh or create new token as needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed existing credentials")
            except Exception as e:
                logger.error(f"Error refreshing token: {str(e)}")
                creds = None

        # If no valid creds, run the OAuth flow
        if not creds:
            oauth_file_path = "/etc/secrets/OAuthClientIDJSON.json"
            try:
                flow = InstalledAppFlow.from_client_secrets_file(oauth_file_path, SCOPES)
                # Use console flow instead of browser flow
                creds = flow.run_console()
                logger.info("Created new credentials through OAuth flow")

                # Save the credentials for the next run
                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)
                    logger.info("Saved new credentials to token file")
            except Exception as e:
                logger.error(f"OAuth flow failed: {str(e)}")
                raise

    # Build and return the calendar service
    return build("calendar", "v3", credentials=creds)
