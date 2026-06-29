from typing import Generator
import google.generativeai as genai
from core.config import groq_client, GROQ_MODEL, GEMINI_MODEL
from core.memory import log_error


def call_with_fallback(
    agent_name:    str,
    messages:      list,
    system_prompt: str,
    temperature:   float = 0.5,
    max_tokens:    int   = 1024,
) -> tuple[str, str]:
    """
    Try Groq first. On any failure, fall back to Gemini.
    Returns (reply_text, provider_used).
    """
    # ── Groq attempt ──────────────────────────────────────────────────────────
    try:
        response = groq_client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [{"role": "system", "content": system_prompt}] + messages,
            temperature = temperature,
            max_tokens  = max_tokens,
        )
        return response.choices[0].message.content.strip(), "groq"

    except Exception as groq_err:
        log_error(
            agent    = agent_name,
            provider = "groq",
            error    = str(groq_err),
            fallback = "gemini",
            resolved = False,
        )

    # ── Gemini fallback ───────────────────────────────────────────────────────
    try:
        model    = genai.GenerativeModel(
            model_name         = GEMINI_MODEL,
            system_instruction = system_prompt,
        )
        # Convert history to Gemini format
        history  = [
            {"role": "model" if m["role"] == "assistant" else "user",
             "parts": [m["content"]]}
            for m in messages[:-1]
        ]
        session  = model.start_chat(history=history)
        response = session.send_message(messages[-1]["content"])
        reply    = response.text.strip()

        log_error(
            agent    = agent_name,
            provider = "groq",
            error    = "Groq failed — used Gemini fallback",
            fallback = "gemini",
            resolved = True,
        )
        return reply, "gemini (fallback)"

    except Exception as gemini_err:
        log_error(
            agent    = agent_name,
            provider = "gemini",
            error    = str(gemini_err),
            fallback = "none",
            resolved = False,
        )
        return (
            "⚠️ Both Groq and Gemini are currently unavailable. "
            "Please check your API keys and try again.",
            "none"
        )


def call_stream_with_fallback(
    agent_name:    str,
    messages:      list,
    system_prompt: str,
    temperature:   float = 0.5,
) -> Generator[str, None, None]:
    """
    Streaming version — tries Groq stream first, falls back to Gemini stream.
    Yields tokens as they arrive.
    Yields a special sentinel prefix '⚠️FALLBACK:' if switching providers,
    so the UI can show a notice.
    """
    # ── Groq streaming attempt ────────────────────────────────────────────────
    try:
        stream = groq_client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [{"role": "system", "content": system_prompt}] + messages,
            temperature = temperature,
            stream      = True,
        )
        for chunk in stream:
            yield chunk.choices[0].delta.content or ""
        return  # success — done

    except Exception as groq_err:
        log_error(
            agent    = agent_name,
            provider = "groq",
            error    = str(groq_err),
            fallback = "gemini",
            resolved = False,
        )
        yield "\n\n⚡ *Groq unavailable — switching to Gemini...*\n\n"

    # ── Gemini streaming fallback ─────────────────────────────────────────────
    try:
        model   = genai.GenerativeModel(
            model_name         = GEMINI_MODEL,
            system_instruction = system_prompt,
        )
        history = [
            {"role": "model" if m["role"] == "assistant" else "user",
             "parts": [m["content"]]}
            for m in messages[:-1]
        ]
        session  = model.start_chat(history=history)
        stream   = session.send_message(messages[-1]["content"], stream=True)

        for chunk in stream:
            yield chunk.text or ""

        log_error(
            agent    = agent_name,
            provider = "groq",
            error    = "Groq stream failed — used Gemini fallback",
            fallback = "gemini",
            resolved = True,
        )

    except Exception as gemini_err:
        log_error(
            agent    = agent_name,
            provider = "gemini",
            error    = str(gemini_err),
            fallback = "none",
            resolved = False,
        )
        yield (
            "\n\n⚠️ **Both Groq and Gemini are currently unavailable.** "
            "Please check your API keys and try again."
        )