from base64 import urlsafe_b64decode
from io import StringIO
import os
from time import sleep

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload


class MailProcessor:
    def __init__(self, credentials: Credentials, catch_all_label_id: str):
        self.credentials = credentials
        self.catch_all_label_id = catch_all_label_id

        self.gmail_client = build("gmail", "v1", credentials=credentials)
        self.groups_client = build("admin", "directory_v1", credentials=credentials)
        self.group_settings_client = build("groupssettings", "v1", credentials=credentials)
        self.group_archive_client = build("groupsmigration", "v1", credentials=credentials)

    def work_indefinitely(self):
        while True:
            if not self.find_and_process_new_mails():
                sleep(10)

    def find_and_process_new_mails(self) -> bool:
        new_messages = self.gmail_client.users().messages().list(
            userId="me",
            labelIds=[self.catch_all_label_id],
            includeSpamTrash=False,
        ).execute()

        if new_messages.get("messages", []):
            for message in new_messages.get("messages"):
                self.process_mail(message.get("id"))

            return True

        return False

    def process_mail(self, message_id: str):
        message = self.gmail_client.users().messages().get(userId="me", id=message_id, format="full").execute()

        original_recipient = next((h["value"] for h in message['payload']['headers'] if h["name"] == "To"), None)

        subject = next((h["value"] for h in message['payload']['headers'] if h["name"] == "Subject"), None)

        print(f"Starting processing of new message '{subject}'...")

        assert original_recipient

        self.find_or_create_group(original_recipient)

        self.copy_email_to_group(original_recipient, message)

        self.move_email_to_inbox(message)

        print(f"Processed message '{subject}'!")

    def find_or_create_group(self, group_address: str):
        try:
            self.groups_client.groups().get(groupKey=group_address).execute()
        except HttpError as error:
            if error.status_code == 404:
                self.create_and_setup_group(group_address)
            else:
                raise

    def create_and_setup_group(self, group_address: str):
        self.groups_client.groups().insert(body={
            "email": group_address,
            "name": group_address.split("@")[0].capitalize(),
            "description": "An automatic group created to group emails sent to this e-mail address in",
        }).execute()

        self.groups_client.members().insert(groupKey=group_address, body={
            "email": os.environ.get("MAIN_EMAIL_ADDRESS", ""),
            "role": "OWNER",
            "delivery_settings": "ALL_MAIL",
        }).execute()

    def copy_email_to_group(self, group_address: str, message: dict):
        raw_mail = self.gmail_client.users().messages().get(userId="me", id=message['id'], format="raw").execute()

        mail_body = StringIO(urlsafe_b64decode(raw_mail['raw']).decode("utf-8"))
        mail = MediaIoBaseUpload(mail_body, mimetype="message/rfc822")

        self.group_archive_client.archive().insert(groupId=group_address, media_body=mail).execute()

    def move_email_to_inbox(self, message: dict):
        self.gmail_client.users().messages().modify(userId="me", id=message["id"], body={
            "addLabelIds": ["INBOX"],
            "removeLabelIds": [self.catch_all_label_id]
        }).execute()
