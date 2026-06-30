import re

MAX_MESSAGE_LENGTH = 4000
MIN_MESSAGE_LENGTH = 1

# Patterns that suggest someone is trying to override the system prompt
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|above|prior) instructions",
    r"disregard (all )?(previous|above|prior) (instructions|rules)",
    r"you are now",
    r"system prompt",
    r"reveal your (instructions|prompt|system message)",
    r"act as if you have no (restrictions|rules|guidelines)",
]

# Basic spam / abuse signals — repeated chars, excessive caps, etc.
SPAM_REPEAT_CHAR_PATTERN = re.compile(r"(.)\1{9,}")  # same char 10+ times in a row


def _looks_like_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)


def _looks_like_spam(text: str) -> bool:
    if SPAM_REPEAT_CHAR_PATTERN.search(text):
        return True
    # Excessive caps ratio on long messages (likely shouting/spam, not a real query)
    letters = [c for c in text if c.isalpha()]
    if len(letters) > 30:
        caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if caps_ratio > 0.85:
            return True
    return False


def validate_user_input(message: str) -> tuple[bool, str, str]:
    """
    Validates and sanitizes raw user input before it reaches any agent.

    Returns:
        (True,  cleaned_message, "")            if input passes all checks
        (False, "",               error_message) if input should be blocked
    """
    if message is None:
        return False, "", "⚠️ Empty message received. Please type something."

    cleaned = message.strip()

    if len(cleaned) < MIN_MESSAGE_LENGTH:
        return False, "", "⚠️ Your message appears to be empty. Please type a question or request."

    if len(cleaned) > MAX_MESSAGE_LENGTH:
        return False, "", (
            f"⚠️ Your message is too long ({len(cleaned)} characters). "
            f"Please keep it under {MAX_MESSAGE_LENGTH} characters."
        )

    if _looks_like_injection(cleaned):
        return False, "", (
            "⚠️ This message looks like it's trying to override the assistant's "
            "instructions, which isn't allowed. Please rephrase your actual request."
        )

    if _looks_like_spam(cleaned):
        return False, "", (
            "⚠️ This message looks like spam or accidental repeated input. "
            "Please rephrase and try again."
        )

    return True, cleaned, ""


def validate_email_address(email: str) -> bool:
    """Basic RFC-5322-lite email validation used before any real Gmail send."""
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email.strip()))


def validate_date_format(date_str: str) -> bool:
    """Validates YYYY-MM-DD format used by the Calendar Agent before create_event()."""
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate_time_format(time_str: str) -> bool:
    """Validates HH:MM 24-hour format used by the Calendar Agent before create_event()."""
    from datetime import datetime
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False