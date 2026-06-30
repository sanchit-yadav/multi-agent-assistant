import json
from typing import Generator
from core.fallback import call_with_fallback, call_stream_with_fallback
from core.memory import log_action, log_error
from core.guardrails import validate_date_format, validate_time_format
from tools.calendar_tool import create_event, list_events

SYSTEM_PROMPT = """You are a Calendar Agent connected to real Google Calendar.

You have two real actions:

1. To CREATE an event, reply ONLY with this exact JSON (no other text):
{"action": "create", "title": "Event title", "date": "YYYY-MM-DD", "time": "HH:MM", "duration_hours": 1, "description": "Optional description"}

2. To LIST upcoming events, reply ONLY with this exact JSON (no other text):
{"action": "list", "days_ahead": 7}

3. For scheduling advice or general questions, reply normally as plain text.

Always ask for date and time if not clearly provided. Use 24-hour time format."""


class CalendarAgent:
    def __init__(self):
        self.name     = "Calendar Agent"
        self.provider = "Groq → Gemini fallback"
        self.history  = []

    def _handle_action(self, reply: str) -> str | None:
        try:
            data   = json.loads(reply)
            action = data.get("action")

            if action == "create":
                event_date = data.get("date", "")
                event_time = data.get("time", "")

                if not validate_date_format(event_date):
                    log_action("calendar", "create_event",
                               f"Blocked — invalid date format: {event_date}", "error")
                    return (
                        f"⚠️ '{event_date}' isn't a valid date. Please provide a date "
                        f"in YYYY-MM-DD format (e.g. 2025-07-01)."
                    )

                if not validate_time_format(event_time):
                    log_action("calendar", "create_event",
                               f"Blocked — invalid time format: {event_time}", "error")
                    return (
                        f"⚠️ '{event_time}' isn't a valid time. Please provide a time "
                        f"in 24-hour HH:MM format (e.g. 14:30)."
                    )

                try:
                    result = create_event(
                        title          = data["title"],
                        date           = data["date"],
                        time           = data["time"],
                        duration_hours = int(data.get("duration_hours", 1)),
                        description    = data.get("description", ""),
                    )
                    log_action("calendar", "create_event", data["title"], "success")
                    return f"✅ {result}"
                except Exception as e:
                    log_action("calendar", "create_event", str(e), "error")
                    log_error("calendar", "google_calendar", str(e))
                    return (
                        f"❌ Could not create event: {str(e)}\n\n"
                        f"Make sure your Google Calendar OAuth is set up correctly.\n\n"
                        f"**Event details (save manually):**\n"
                        f"📅 {data.get('title')} on {data.get('date')} at {data.get('time')}"
                    )

            elif action == "list":
                try:
                    events = list_events(days_ahead=int(data.get("days_ahead", 7)))
                    log_action("calendar", "list_events",
                               f"Fetched {len(events)} events", "success")
                    if not events:
                        return f"📅 No upcoming events in the next {data.get('days_ahead', 7)} days."
                    lines = [f"📅 **Upcoming events (next {data.get('days_ahead', 7)} days):**\n"]
                    for e in events:
                        lines.append(f"• **{e['title']}** — {e['start']}")
                    return "\n".join(lines)
                except Exception as e:
                    log_action("calendar", "list_events", str(e), "error")
                    log_error("calendar", "google_calendar", str(e))
                    return f"❌ Could not fetch calendar events: {str(e)}"

        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        reply, _ = call_with_fallback("calendar", self.history, SYSTEM_PROMPT, temperature=0.2)

        action_result = self._handle_action(reply)
        if action_result:
            reply = action_result

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        self.history.append({"role": "user", "content": user_message})

        peek, _ = call_with_fallback(
            "calendar", self.history, SYSTEM_PROMPT, temperature=0.2, max_tokens=60
        )

        if peek.strip().startswith("{"):
            self.history.pop()
            result = self.chat(user_message)
            yield result
            return

        full_reply = ""
        for token in call_stream_with_fallback("calendar", self.history, SYSTEM_PROMPT, temperature=0.2):
            full_reply += token
            yield token

        self.history.append({"role": "assistant", "content": full_reply})

    def reset(self):
        self.history = []
