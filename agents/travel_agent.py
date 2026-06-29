import json
from typing import Generator
from core.fallback import call_with_fallback, call_stream_with_fallback
from core.memory import log_action, log_error
from tools.maps_tool import search_place, get_nearby_places

SYSTEM_PROMPT = """You are a Travel Planning Agent with access to real map data via OpenStreetMap.

You have two location tools:

1. To look up a place, reply ONLY with this JSON (no other text):
{"action": "search_place", "query": "place name, country"}

2. To find nearby attractions, reply ONLY with this JSON (no other text):
{"action": "nearby", "lat": "latitude", "lon": "longitude", "category": "tourism"}

3. For itinerary planning, travel tips, packing lists, or general advice, reply normally as plain text.

Workflow: Search destination → get coordinates → find nearby → build itinerary.
Always ask about budget, trip duration, travel dates, group size if not mentioned."""


class TravelAgent:
    def __init__(self):
        self.name     = "Travel Agent"
        self.provider = "Groq → Gemini fallback"
        self.history  = []

    def _handle_map_action(self, reply: str) -> str | None:
        try:
            data   = json.loads(reply)
            action = data.get("action")

            if action == "search_place":
                try:
                    place = search_place(data["query"])
                    log_action("travel", "search_place", data["query"], "success")
                    if "error" in place:
                        return f"Location lookup failed: {place['error']}"
                    return f"Map data for '{data['query']}':\n{json.dumps(place, indent=2)}"
                except Exception as e:
                    log_action("travel", "search_place", str(e), "error")
                    log_error("travel", "openstreetmap", str(e))
                    return f"Could not look up location '{data.get('query')}': {str(e)}"

            elif action == "nearby":
                try:
                    places = get_nearby_places(
                        data["lat"], data["lon"], data.get("category", "tourism")
                    )
                    log_action("travel", "nearby_places",
                               f"lat={data['lat']}, lon={data['lon']}", "success")
                    if places:
                        text = "\n".join([f"- {p['name']} ({p['type']})" for p in places])
                    else:
                        text = "No nearby attractions found in the OpenStreetMap database."
                    return f"Nearby places:\n{text}"
                except Exception as e:
                    log_action("travel", "nearby_places", str(e), "error")
                    log_error("travel", "openstreetmap", str(e))
                    return f"Could not fetch nearby places: {str(e)}"

        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        reply, _ = call_with_fallback("travel", self.history, SYSTEM_PROMPT, temperature=0.5)

        tool_result = self._handle_map_action(reply)
        if tool_result:
            self.history.append({"role": "assistant", "content": reply})
            self.history.append({"role": "user",      "content": tool_result})
            reply, _ = call_with_fallback("travel", self.history, SYSTEM_PROMPT, temperature=0.5)

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        self.history.append({"role": "user", "content": user_message})

        peek, _ = call_with_fallback(
            "travel", self.history, SYSTEM_PROMPT, temperature=0.5, max_tokens=60
        )
        tool_result = self._handle_map_action(peek)

        if tool_result:
            yield "🗺️ *Looking up location data...*\n\n"
            self.history.append({"role": "assistant", "content": peek})
            self.history.append({"role": "user",      "content": tool_result})

            full_reply = ""
            for token in call_stream_with_fallback("travel", self.history, SYSTEM_PROMPT, temperature=0.5):
                full_reply += token
                yield token
            self.history.append({"role": "assistant", "content": full_reply})
        else:
            full_reply = ""
            for token in call_stream_with_fallback("travel", self.history, SYSTEM_PROMPT, temperature=0.5):
                full_reply += token
                yield token
            self.history.append({"role": "assistant", "content": full_reply})

    def reset(self):
        self.history = []