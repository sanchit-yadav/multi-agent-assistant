import streamlit as st
from datetime import datetime, timedelta

# ── Configurable limits ────────────────────────────────────────────────────────
MAX_MESSAGES_PER_SESSION = 15      # total messages allowed per browser session
MAX_MESSAGES_PER_MINUTE  = 5       # burst protection — messages allowed per 60s window


def _init_state():
    if "rl_total_count" not in st.session_state:
        st.session_state.rl_total_count = 0
    if "rl_window_start" not in st.session_state:
        st.session_state.rl_window_start = datetime.now()
    if "rl_window_count" not in st.session_state:
        st.session_state.rl_window_count = 0


def check_rate_limit() -> tuple[bool, str]:
    """
    Call this BEFORE processing any user message.
    Returns (allowed: bool, message: str).
    If allowed is False, the caller should show `message` and stop processing.
    """
    _init_state()

    # ── Total session limit ──────────────────────────────────────────────────
    if st.session_state.rl_total_count >= MAX_MESSAGES_PER_SESSION:
        return False, (
            f"🛑 **Demo limit reached** ({MAX_MESSAGES_PER_SESSION} messages per session). "
            f"This protects the free-tier API quota for everyone testing this demo. "
            f"Clone the repo from GitHub to run your own unlimited instance."
        )

    # ── Burst limit (sliding 60s window) ─────────────────────────────────────
    now = datetime.now()
    if now - st.session_state.rl_window_start > timedelta(seconds=60):
        st.session_state.rl_window_start = now
        st.session_state.rl_window_count = 0

    if st.session_state.rl_window_count >= MAX_MESSAGES_PER_MINUTE:
        seconds_left = 60 - int((now - st.session_state.rl_window_start).total_seconds())
        return False, (
            f"🛑 **Slow down!** Max {MAX_MESSAGES_PER_MINUTE} messages per minute. "
            f"Please wait {max(seconds_left, 1)} seconds and try again."
        )

    return True, ""


def record_request():
    """Call this AFTER a message is successfully processed to increment counters."""
    _init_state()
    st.session_state.rl_total_count  += 1
    st.session_state.rl_window_count += 1


def get_usage() -> dict:
    """Returns current usage stats — useful for showing a 'X messages remaining' badge."""
    _init_state()
    return {
        "used":      st.session_state.rl_total_count,
        "limit":     MAX_MESSAGES_PER_SESSION,
        "remaining": max(MAX_MESSAGES_PER_SESSION - st.session_state.rl_total_count, 0),
    }