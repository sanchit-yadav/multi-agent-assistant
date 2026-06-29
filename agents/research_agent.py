from typing import Generator
import google.generativeai as genai
from core.config import GEMINI_MODEL, groq_client, GROQ_MODEL
from core.memory import log_action, log_error
from tools.search_tool import search

SYSTEM_PROMPT = """You are a Research Agent with access to live web search results.
You receive the user query plus real-time search results.
Provide a well-structured, comprehensive answer with:
- Key findings and important details
- Cited sources with URLs
- Your analysis and summary
Be thorough but easy to read. Use bullet points and sections."""


class ResearchAgent:
    def __init__(self):
        self.name     = "Research Agent"
        self.provider = "Gemini 2.5 Flash → Groq fallback"
        self.history  = []
        self._init_gemini()

    def _init_gemini(self):
        self.model   = genai.GenerativeModel(
            model_name         = GEMINI_MODEL,
            system_instruction = SYSTEM_PROMPT,
        )
        self.session = self.model.start_chat(history=[])

    def _build_enriched(self, user_message: str) -> str:
        try:
            results = search(user_message, max_results=5)
            log_action("research", "web_search", user_message, "success")
        except Exception as e:
            log_error("research", "tavily", str(e))
            log_action("research", "web_search", str(e), "error")
            results = []

        if results:
            context = "\n\n".join([
                f"Source {i+1}: {r['title']}\nURL: {r['url']}\n{r['content']}"
                for i, r in enumerate(results)
            ])
            return (
                f"User question: {user_message}\n\n"
                f"Live web search results:\n{context}\n\n"
                f"Answer using these results and cite sources."
            )
        return f"User question: {user_message}\n\n(No search results available — answer from your knowledge.)"

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        enriched = self._build_enriched(user_message)

        # Try Gemini first
        try:
            response = self.session.send_message(enriched)
            reply    = response.text
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as gemini_err:
            log_error("research", "gemini", str(gemini_err), "groq", False)

        # Groq fallback
        try:
            response = groq_client.chat.completions.create(
                model    = GROQ_MODEL,
                messages = [{"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user",   "content": enriched}],
            )
            reply = response.choices[0].message.content.strip()
            log_error("research", "gemini", "Gemini failed — used Groq fallback", "groq", True)
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as groq_err:
            log_error("research", "groq", str(groq_err), "none", False)
            reply = "⚠️ Both Gemini and Groq are currently unavailable. Please try again later."
            self.history.append({"role": "assistant", "content": reply})
            return reply

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        self.history.append({"role": "user", "content": user_message})
        enriched = self._build_enriched(user_message)

        # Try Gemini stream
        try:
            stream     = self.session.send_message(enriched, stream=True)
            full_reply = ""
            for chunk in stream:
                token       = chunk.text or ""
                full_reply += token
                yield token
            self.history.append({"role": "assistant", "content": full_reply})
            return
        except Exception as gemini_err:
            log_error("research", "gemini", str(gemini_err), "groq", False)
            yield "\n\n⚡ *Gemini unavailable — switching to Groq...*\n\n"

        # Groq stream fallback
        try:
            stream = groq_client.chat.completions.create(
                model    = GROQ_MODEL,
                messages = [{"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user",   "content": enriched}],
                stream   = True,
            )
            full_reply = ""
            for chunk in stream:
                token       = chunk.choices[0].delta.content or ""
                full_reply += token
                yield token
            log_error("research", "gemini", "Gemini stream failed — used Groq", "groq", True)
            self.history.append({"role": "assistant", "content": full_reply})
        except Exception as groq_err:
            log_error("research", "groq", str(groq_err), "none", False)
            yield "\n\n⚠️ **Both providers are unavailable. Please try again later.**"

    def reset(self):
        self.history = []
        self._init_gemini()