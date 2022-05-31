"""
Steps:
1. Run and check for GCloud credentials
2. Launch interactive flow to gain credentials
3. Find label like "Catch-All" in GMail for authenticated user
4. Set up watcher to GMail PubSub for new e-mails
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource
from googleapiclient.discovery import build

from workspace_groups_creator.mail_processor import MailProcessor

SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/apps.groups.settings"
]


def get_credentials() -> Credentials:
    client_secret_path = os.environ["CLIENT_SECRET_PATH"] if "CLIENT_SECRET_PATH" in os.environ else \
        Path(os.getcwd()) / "../client_secret.json"

    assert os.path.exists(client_secret_path)

    installed_app_flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes=SCOPES)

    received_credentials = installed_app_flow.run_local_server(open_browser=False)

    return received_credentials


def find_label_id(gmail_client: Resource) -> str:
    labels = gmail_client.users().labels().list(userId="me").execute()

    found_label_id = next((label['id'] for label in labels.get("labels", []) if
                    label['name'].upper() == os.environ.get("GMAIL_CATCHALL_LABEL_NAME", "Catch-All").upper()), None)

    assert found_label_id

    return found_label_id


if __name__ == "__main__":
    load_dotenv()

    credentials = get_credentials()

    client: Resource = build("gmail", 'v1', credentials=credentials)

    label_id = find_label_id(client)

    client.close()

    MailProcessor(credentials, label_id).work_indefinitely()
