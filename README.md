# 🤖 Multi-Agent Personal Assistant

> An AI-powered personal assistant that orchestrates 4 specialized agents — Email, Research, Calendar, and Travel — with multi-provider LLM fallback, real Google APIs, live web search, agent collaboration, input guardrails, and persistent memory.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-blue?logo=google)
![SQLite](https://img.shields.io/badge/Memory-SQLite-lightgrey?logo=sqlite)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest)
![License](https://img.shields.io/badge/License-MIT-green)


## 🚀 Live Demo
[Click here to view the deployed project](https://multi-agent-assistant-oxdrukcj9xtapruvcettv5.streamlit.app/)

---

## 🎥 Demo

### Agent Collaboration
![Collaborate demo](Demo/demo-collaborate.gif)

### Real-time Streaming
![Streaming demo](Demo/demo-streaming.gif)

### Logs Dashboard
![Dashboard demo](Demo/demo-dashboard.gif)


**⚠️ Demo deployment notice:** The public Streamlit Cloud link does **not** use the developer's personal Gmail/Calendar credentials. Email and Calendar agents draft content correctly, but real send/create actions require your own API keys and Google OAuth setup — see [Quick Start](#-quick-start) below.

---

## 🏗️ Architecture


```
User Input
    │
    ▼
┌───────────────────────────────────┐
│  Guardrails (core/guardrails.py)  │  ← blocks empty/oversized/injection input
└──────┬────────────────────────────┘
       ▼
┌───────────────────────────────────┐
│  Rate Limiter (core/rate_limiter) │  ← 15 msgs/session, 5 msgs/min per browser
└──────┬────────────────────────────┘
       ▼
┌───────────────────────────────────┐
│   Orchestrator (Groq Llama 3.3)   │  ← classifies intent, detects collaboration
│   routes to 1 or 2 agents         │
└──────┬──────┬──────┬──────┬───────┘
       │      │      │      │
       ▼      ▼      ▼      ▼
  📧 Email  🔍 Research  📅 Calendar  ✈️ Travel
  Agent     Agent        Agent        Agent
  (Groq)   (Gemini)     (Groq)       (Groq)
     │          │            │            │
     ▼          ▼            ▼            ▼
  Gmail     Tavily       Google       OpenStreet
  API       Search       Calendar     Map API
                         API
       │      │      │      │
       └──────┴──────┴──────┘
                   │
                   ▼
          SQLite Memory (per-agent)
          + Action Logs + Error Logs
```

### Provider Fallback (every agent)
```
Groq fails → auto-switch to Gemini → log error to SQLite → continue seamlessly
```

### Agent Collaboration (new)
```
"Research best time to visit Japan and add a calendar reminder"
   → Research Agent answers (Step 1)
   → hands its output as context to Calendar Agent
   → Calendar Agent acts on it (Step 2)
   → both steps shown in the UI
```

---

## ✨ Features

- **4 Specialized Agents** — each with its own system prompt, LLM provider, and memory
- **Auto-routing** — Groq Llama 3.3 classifies user intent and routes to the right agent
- **Agent-to-agent collaboration** — a dedicated "Collaborate" mode where one agent's output feeds another (e.g. Research → Calendar)
- **Real Gmail integration** — send emails and read inbox via Gmail API (OAuth2)
- **Real Google Calendar integration** — create and list events via Calendar API (OAuth2)
- **Live web search** — Research Agent uses Tavily for real-time search results
- **Real map data** — Travel Agent uses OpenStreetMap for location lookup and nearby places
- **Streaming responses** — token-by-token output like ChatGPT using Groq LPU
- **Provider fallback** — if Groq fails, auto-switches to Gemini without interruption
- **Input guardrails** — blocks empty/oversized messages, prompt-injection attempts, spam patterns, and validates emails/dates/times before they reach any real API
- **Rate limiting** — per-session message caps protect free-tier API quota on public deployments
- **Persistent memory** — SQLite stores conversation history per agent across sessions
- **Logs dashboard** — real-time action logs, error logs, success rate, and charts
- **22 unit tests** — pytest suite covering routing, memory, tools, and guardrails

---

## 🤖 Agent Overview

| Agent | Provider | Tools | Capabilities |
|-------|----------|-------|--------------|
| 📧 Email | Groq Llama 3.3 → Gemini fallback | Gmail API | Draft, send, read inbox (email format validated) |
| 🔍 Research | Gemini 2.5 Flash → Groq fallback | Tavily Search | Live web research, summaries, analysis |
| 📅 Calendar | Groq Llama 3.3 → Gemini fallback | Google Calendar API | Create events, list schedule (date/time format validated) |
| ✈️ Travel | Groq Llama 3.3 → Gemini fallback | OpenStreetMap | Itineraries, location lookup, nearby places |
| 🧭 Orchestrator | Groq Llama 3.3 | — | Intent classification, single/collaborative routing |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| UI | Streamlit |
| LLM (Orchestrator + 3 agents) | Groq — Llama 3.3 70B Versatile |
| LLM (Research Agent) | Google Gemini 2.5 Flash |
| LLM Fallback | Groq ↔ Gemini auto-switch on every agent |
| Email | Gmail API (OAuth2) |
| Calendar | Google Calendar API (OAuth2) |
| Search | Tavily API |
| Maps | OpenStreetMap Nominatim + Overpass API |
| Memory | SQLite (conversation history + action logs + error logs) |
| Testing | pytest + unittest.mock (22 tests, no live API calls) |
| Safety | Custom guardrails module + session-based rate limiter |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/sanchit-yadav/multi-agent-assistant
cd multi-agent-assistant
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API keys
```bash
cp .env.example .env
```
Open `.env` and fill in:
```env
GROQ_API_KEY=your_key       # free at console.groq.com
GEMINI_API_KEY=your_key     # free at aistudio.google.com
TAVILY_API_KEY=your_key     # free at app.tavily.com
```

### 5. Set up Google OAuth (Gmail + Calendar)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → Enable **Gmail API** + **Google Calendar API**
3. Credentials → Create **OAuth 2.0 Client ID** → Desktop App
4. Download JSON → rename to `credentials.json` → place in `auth/` folder
5. On first run, a browser tab opens for Google login — approve it once, never again

### 6. Run
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

### 7. Run the test suite
```bash
pytest tests/ -v
```


---

## 💬 Usage Examples

### Auto-Route Mode
```
"Plan a 5-day trip to Goa on a budget of ₹3000/day"     → Travel Agent
"What are the latest developments in AI in 2025?"         → Research Agent
"Schedule a team standup every Monday at 10am"            → Calendar Agent
"Write a follow-up email to a client who hasn't replied"  → Email Agent
```

### Collaborate Mode
```
"Research the best time to visit Japan and add a calendar reminder"
   → Research Agent finds the answer
   → Calendar Agent creates a reminder using that answer
```

### Manual Mode
Click an agent in the sidebar to lock it:
```
📧 Email     → Draft and send real emails via Gmail
🔍 Research  → Get live web-searched answers with sources
📅 Calendar  → Create and view real Google Calendar events
✈️ Travel    → Build itineraries with real map data
```

---

## 🛡️ Safety & Reliability

- **Guardrails** (`core/guardrails.py`) reject empty input, oversized input (>4000 chars), prompt-injection attempts, and spam patterns before anything reaches an LLM
- **Email/date/time validation** runs before any real Gmail send or Calendar event creation — malformed LLM output is caught, not executed
- **Rate limiting** (`core/rate_limiter.py`) caps each browser session to 15 messages total / 5 per minute, protecting shared-deployment API quota
- **Provider fallback** (`core/fallback.py`) — every agent retries on Gemini if Groq fails, with the failure and resolution logged to SQLite

---

## 📊 Logs Dashboard

Built-in **Logs Dashboard** tab showing:
- Total actions, success rate, error count, auto-resolved errors
- Actions per agent (bar chart) and conversation length per agent
- Full action log table with status highlighting
- Error & fallback log — which provider failed and whether fallback resolved it

---

## 🧪 Testing

```
tests/
  test_orchestrator.py   → 6 tests: intent routing, malformed-JSON handling
  test_memory.py         → 4 tests: SQLite save/load/clear/log roundtrips
  test_tools.py          → 4 tests: maps tool, action-JSON schema validation
  test_guardrails.py     → 8 tests: injection blocking, email/date validation
```
All LLM calls are mocked with `unittest.mock` — the suite runs in seconds with zero API usage.

---

## 📁 Project Structure

```
multi_agent_assistant/
  agents/
    email_agent.py        ← Gmail API + Groq (validated email format)
    research_agent.py     ← Tavily search + Gemini
    calendar_agent.py     ← Google Calendar + Groq (validated date/time)
    travel_agent.py       ← OpenStreetMap + Groq
  core/
    orchestrator.py       ← Groq routing + collaborate() for agent handoff
    fallback.py            ← Groq → Gemini auto-fallback
    guardrails.py          ← input validation, injection/spam blocking
    rate_limiter.py        ← per-session message caps
    memory.py              ← SQLite (history + action/error logs)
    config.py               ← API clients (reads Streamlit secrets or .env)
  tools/
    gmail_tool.py          ← send/read Gmail
    calendar_tool.py       ← create/list events
    search_tool.py         ← Tavily web search
    maps_tool.py            ← OpenStreetMap lookup
  auth/
    google_auth.py         ← OAuth2 flow
  tests/
    test_orchestrator.py
    test_memory.py
    test_tools.py
    test_guardrails.py
  app.py                   ← Streamlit UI (Chat + Collaborate + Dashboard)
  pytest.ini
  requirements.txt
  .env.example
```

---

## 🔮 Upcoming Features

- [ ] RAG with ChromaDB for semantic memory search
- [ ] CI/CD with GitHub Actions running pytest on every push
- [ ] Expanded collaboration flows (3+ agent chains)

---

## 📄 License

MIT License — free to use, modify, and share.

---

## 🙋 Author

**Sanchit Yadav**
[LinkedIn](https://www.linkedin.com/in/sanchit-yadav-26a849341/) • [GitHub](https://github.com/sanchit-yadav)
