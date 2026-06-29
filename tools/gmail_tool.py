import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from auth.google_auth import get_google_credentials


def _service():
    return build("gmail", "v1", credentials=get_google_credentials())


def send_email(to: str, subject: str, body: str) -> str:
    message            = MIMEText(body)
    message["to"]      = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    _service().users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"Email successfully sent to {to} with subject '{subject}'."


def read_emails(max_results: int = 5) -> list:
    results  = _service().users().messages().list(
        userId="me", maxResults=max_results, labelIds=["INBOX"]
    ).execute()
    messages = results.get("messages", [])
    emails   = []
    for msg in messages:
        detail  = _service().users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        emails.append({
            "from":    headers.get("From", "Unknown"),
            "subject": headers.get("Subject", "No subject"),
            "date":    headers.get("Date", ""),
        })
    return emails