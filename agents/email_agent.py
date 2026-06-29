import json
from typing import Generator
from core.fallback import call_with_fallback, call_stream_with_fallback
from core.memory import log_action, log_error
from tools.gmail_tool import send_email, read_emails

SYSTEM_PROMPT = """You are a professional Email Agent connected to real Gmail.

You have two real actions available:

1. To SEND an email, reply ONLY with this exact JSON (no other text):
{"action": "send", "to": "recipient@email.com", "subject": "Subject here", "body": "Full email body here"}

2. To READ inbox, reply ONLY with this exact JSON (no other text):
{"action": "read"}

3. For drafting an email without sending, or for any writing advice, reply normally as plain text.

Rules:
- Always ask for the recipient email address if not provided.
- Always confirm before sending.
- Keep emails professional with greeting and sign-off."""


class EmailAgent:
    def __init__(self):
        self.name     = "Email Agent"
        self.provider = "Groq → Gemini fallback"
        self.history  = []

    def _handle_action(self, reply: str) -> str | None:
        """If reply is a JSON action, execute it and return result string. Else None."""
        try:
            data   = json.loads(reply)
            action = data.get("action")

            if action == "send":
                try:
                    result = send_email(data["to"], data["subject"], data["body"])
                    log_action("email", "send_email",
                               f"To: {data['to']} | Subject: {data['subject']}", "success")
                    return (
                        f"✅ {result}\n\n"
                        f"**Email Preview:**\n"
                        f"**To:** {data['to']}\n"
                        f"**Subject:** {data['subject']}\n\n"
                        f"{data['body']}"
                    )
                except Exception as e:
                    log_action("email", "send_email", str(e), "error")
                    log_error("email", "gmail", str(e))
                    return f"❌ Failed to send email: {str(e)}\n\nHere is the draft:\n\n{data.get('body', '')}"

            elif action == "read":
                try:
                    emails = read_emails(max_results=5)
                    log_action("email", "read_inbox", f"Fetched {len(emails)} emails", "success")
                    if not emails:
                        return "📭 Your inbox appears to be empty."
                    lines = ["📬 **Latest emails in your inbox:**\n"]
                    for i, e in enumerate(emails, 1):
                        lines.append(f"**{i}.** From: {e['from']}")
                        lines.append(f"   Subject: {e['subject']}")
                        lines.append(f"   Date: {e['date']}\n")
                    return "\n".join(lines)
                except Exception as e:
                    log_action("email", "read_inbox", str(e), "error")
                    log_error("email", "gmail", str(e))
                    return f"❌ Could not read inbox: {str(e)}\n\nMake sure your Gmail OAuth is set up correctly."

        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        reply, _ = call_with_fallback("email", self.history, SYSTEM_PROMPT, temperature=0.3)

        action_result = self._handle_action(reply)
        if action_result:
            reply = action_result

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        self.history.append({"role": "user", "content": user_message})

        # Peek to detect JSON action
        peek, _ = call_with_fallback(
            "email", self.history, SYSTEM_PROMPT, temperature=0.3, max_tokens=60
        )

        if peek.strip().startswith("{"):
            # Action detected — run non-streaming
            self.history.pop()
            result = self.chat(user_message)
            yield result
            return

        # Stream the response
        full_reply = ""
        for token in call_stream_with_fallback("email", self.history, SYSTEM_PROMPT, temperature=0.3):
            full_reply += token
            yield token

        self.history.append({"role": "assistant", "content": full_reply})

    def reset(self):
        self.history = []