from datetime import datetime, timedelta
from googleapiclient.discovery import build
from auth.google_auth import get_google_credentials


def _service():
    return build("calendar", "v3", credentials=get_google_credentials())


def create_event(
    title: str,
    date: str,
    time: str,
    duration_hours: int = 1,
    description: str = "",
) -> str:
    start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    end   = start + timedelta(hours=duration_hours)
    event = {
        "summary":     title,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
        "end":   {"dateTime": end.isoformat(),   "timeZone": "Asia/Kolkata"},
    }
    created = _service().events().insert(calendarId="primary", body=event).execute()
    link    = created.get("htmlLink", "N/A")
    return f"Event '{title}' created on {date} at {time}. Link: {link}"


def list_events(days_ahead: int = 7) -> list:
    now    = datetime.utcnow().isoformat() + "Z"
    future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
    result = _service().events().list(
        calendarId  = "primary",
        timeMin     = now,
        timeMax     = future,
        maxResults  = 10,
        singleEvents= True,
        orderBy     = "startTime",
    ).execute()
    events = []
    for e in result.get("items", []):
        start = e["start"].get("dateTime", e["start"].get("date"))
        events.append({"title": e.get("summary", "Untitled"), "start": start})
    return events