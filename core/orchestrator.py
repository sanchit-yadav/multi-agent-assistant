import json
from core.config import groq_client, GROQ_MODEL
from core.guardrails import validate_user_input
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
- "travel"   → trips, destinations, itineraries, hotels, maps, places to visit

If the message clearly needs TWO agents working together
(e.g. "research X and add it to my calendar", "find flights and email me the itinerary"),
reply with the FIRST agent that should act, and add "collaborate": true plus
"next_agent": "<second agent name>" to the JSON.
Example: {"agent": "research", "reason": "needs research first", "collaborate": true, "next_agent": "calendar"}
Only set collaborate=true when the message truly requires both steps."""


class Orchestrator:
    def __init__(self):
        self.agents = {
            "email":    EmailAgent(),
            "research": ResearchAgent(),
            "calendar": CalendarAgent(),
            "travel":   TravelAgent(),
        }

    def detect_agent(self, message: str) -> tuple:
        """Returns (agent_name, reason). Used by simple single-agent routing."""
        data = self._classify(message)
        return data.get("agent", "research"), data.get("reason", "")

    def detect_full(self, message: str) -> dict:
        """Returns the full classification dict, including collaborate/next_agent flags."""
        return self._classify(message)

    def _classify(self, message: str) -> dict:
        try:
            response = groq_client.chat.completions.create(
                model       = GROQ_MODEL,
                messages    = [
                    {"role": "system", "content": ROUTE_PROMPT},
                    {"role": "user",   "content": message},
                ],
                temperature = 0.1,
                max_tokens  = 120,
            )
            raw = response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            if data.get("agent") not in self.agents:
                data["agent"] = "research"
            return data
        except json.JSONDecodeError:
            return {"agent": "research", "reason": "Could not classify — defaulting to Research"}
        except Exception as e:
            return {"agent": "research", "reason": f"Routing error ({str(e)[:60]}) — defaulting to Research"}

    def route(self, message: str):
        """Single-agent routing — validates input first, then dispatches."""
        is_valid, clean_message, validation_msg = validate_user_input(message)
        if not is_valid:
            class _StubAgent:
                name     = "Guardrail"
                provider = "Input Validator"
            return _StubAgent(), validation_msg, "Blocked by input validation"

        name, reason = self.detect_agent(clean_message)
        agent = self.agents[name]
        reply = agent.chat(clean_message)
        return agent, reply, reason

    def collaborate(self, message: str) -> dict:
        """
        Agent-to-agent collaboration.
        Step 1: First agent (e.g. Research) handles the message.
        Step 2: Its output is handed to a second agent (e.g. Calendar) as added
                context, which then takes its own action.
        Returns a dict describing both steps for the UI to render.
        """
        is_valid, clean_message, validation_msg = validate_user_input(message)
        if not is_valid:
            return {
                "collaborated": False,
                "step1_agent": "Guardrail", "step1_reply": validation_msg,
                "step2_agent": None, "step2_reply": None,
            }

        classification = self._classify(clean_message)
        first_name  = classification.get("agent", "research")
        will_collab = classification.get("collaborate", False)
        second_name = classification.get("next_agent")

        first_agent = self.agents[first_name]
        first_reply = first_agent.chat(clean_message)

        if not will_collab or second_name not in self.agents:
            return {
                "collaborated": False,
                "step1_agent": first_agent.name, "step1_reply": first_reply,
                "step2_agent": None, "step2_reply": None,
            }

        second_agent = self.agents[second_name]
        handoff_message = (
            f"Context from {first_agent.name}:\n{first_reply}\n\n"
            f"Original user request: {clean_message}\n\n"
            f"Using the context above, take the appropriate action now."
        )
        second_reply = second_agent.chat(handoff_message)

        return {
            "collaborated": True,
            "step1_agent": first_agent.name, "step1_reply": first_reply,
            "step2_agent": second_agent.name, "step2_reply": second_reply,
        }