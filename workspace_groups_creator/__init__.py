"""
Steps:
1. Run and check for GCloud credentials
2. Launch interactive flow to gain credentials
3. Find label like "Catch-All" in GMail for authenticated user
4. Set up watcher to GMail PubSub for new e-mails
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

from workspace_groups_creator.mail_processor import MailProcessor

SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/apps.groups.settings",
    "https://www.googleapis.com/auth/apps.groups.migration"
]

def start():
    load_dotenv()

    # service_account_key_path = os.environ["SERVICE_ACCOUNT_KEY_PATH"] if "SERVICE_ACCOUNT_KEY_PATH" in os.environ else \
    #     Path(os.getcwd()) / "../service_account_key.json"
    service_account = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])

    service_account_credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        service_account,
        scopes=SCOPES
    )

    credentials = service_account_credentials.create_delegated(os.environ["MAIN_EMAIL_ADDRESS"])

    MailProcessor(credentials).work_indefinitely()
