from google_auth_oauthlib.flow import InstalledAppFlow
import os
import pickle
import sys
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Google API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def generate_token():
    """Generate a new OAuth token for Google Calendar access"""
    # Get absolute path to the credentials file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_file = os.path.join(script_dir, "OAuthClientIDJSON.json")
    token_path = os.path.join(script_dir, "token.json")

    # Check if credentials file exists
    if not os.path.exists(credentials_file):
        logger.error(f"OAuth client secrets file not found at {credentials_file}")
        print(f"ERROR: OAuth Client ID JSON.json not found at {credentials_file}")
        print("Please download OAuth credentials from Google Cloud Console and save them to this location.")
        print("See https://developers.google.com/workspace/guides/create-credentials#oauth-client-id")
        return False

    try:
        logger.info(f"Starting OAuth flow with credentials from {credentials_file}")
        print("Starting OAuth authentication flow...")
        print("A browser window will open. Please login with your Google account and authorize the application.")

        # Create OAuth flow and run local server
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)  # This will open a browser window

        # Save token
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        with open(token_path, "w") as token:
            json.dump(token_data, token)

        logger.info(f"Token successfully generated and saved to {token_path}")
        print(f"Success! Token saved to {token_path}")
        return True

    except Exception as e:
        logger.error(f"Error during OAuth flow: {str(e)}")
        print(f"ERROR: Failed to complete OAuth flow: {str(e)}")
        return False


if __name__ == "__main__":
    success = generate_token()
    sys.exit(0 if success else 1)
