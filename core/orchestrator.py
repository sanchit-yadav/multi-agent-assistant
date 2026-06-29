import json
import google.generativeai as genai
from core.config import groq_client, GROQ_MODEL
from agents.email_agent    import EmailAgent
from agents.research_agent import ResearchAgent
from agents.calendar_agent import CalendarAgent
from agents.travel_agent   import TravelAgent

ROUTE_PROMPT = """You are an intent classifier for a multi-agent assistant.
Classify the user message into exactly one of these agents.
Reply ONLY with valid JSON — no explanation, no markdown, just JSON:
{"agent": "<name>", "reason": "<one short sentence>"}

Agent options:
- "email"    → writing, sending, reading, replying to emails
- "research" → questions, facts, summaries, news, explanations, comparisons
- "calendar" → scheduling, meetings, events, reminders, time planning
- "travel"   → trips, destinations, itineraries, hotels, maps, places to visit"""


class Orchestrator:
    def __init__(self):
        self.agents = {
            "email":    EmailAgent(),
            "research": ResearchAgent(),
            "calendar": CalendarAgent(),
            "travel":   TravelAgent(),
        }

    def detect_agent(self, message: str) -> tuple:
        response = groq_client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [
                {"role": "system", "content": ROUTE_PROMPT},
                {"role": "user",   "content": message}
            ],
            temperature = 0.1,
            max_tokens  = 60,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(raw)
            return data.get("agent", "research"), data.get("reason", "")
        except json.JSONDecodeError:
            return "research", "Could not classify — defaulting to Research"

    def route(self, message: str):
        name, reason = self.detect_agent(message)
        if name not in self.agents:
            name = "research"
        agent = self.agents[name]
        reply = agent.chat(message)
        return agent, reply, reason