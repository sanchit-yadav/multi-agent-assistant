# 🤖 Multi-Agent Personal Assistant

> An AI-powered personal assistant that orchestrates 4 specialized agents — Email, Research, Calendar, and Travel — using multiple LLM providers, real Google APIs, live web search, and persistent memory.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-blue?logo=google)
![SQLite](https://img.shields.io/badge/Memory-SQLite-lightgrey?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎥 Demo

![](./demo.gif)

---

## 🏗️ Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│   Orchestrator (Gemini 2.5 Flash)│  ← classifies intent
│   routes to the right agent      │
└──────┬──────┬──────┬────────────┘
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
          + Action & Error Logs
```

### Provider Fallback
```
Groq fails → auto-switch to Gemini → log error → continue seamlessly
```

---

## ✨ Features

- **4 Specialized Agents** — each with its own system prompt, LLM provider, and memory
- **Auto-routing** — Gemini 2.5 Flash classifies user intent and routes to the right agent
- **Real Gmail integration** — send emails and read inbox via Gmail API (OAuth2)
- **Real Google Calendar integration** — create and list events via Calendar API (OAuth2)
- **Live web search** — Research Agent uses Tavily for real-time search results
- **Real map data** — Travel Agent uses OpenStreetMap for location lookup and nearby places
- **Streaming responses** — token-by-token output like ChatGPT using Groq LPU
- **Provider fallback** — if Groq fails, auto-switches to Gemini without interruption
- **Persistent memory** — SQLite stores conversation history per agent across sessions
- **Logs dashboard** — real-time action logs, error logs, success rate, and charts

---

## 🤖 Agent Overview

| Agent | Provider | Tools | Capabilities |
|-------|----------|-------|--------------|
| 📧 Email | Groq Llama 3.3 | Gmail API | Draft, send, read inbox |
| 🔍 Research | Gemini 2.5 Flash | Tavily Search | Live web research, summaries, analysis |
| 📅 Calendar | Groq Llama 3.3 | Google Calendar API | Create events, list schedule |
| ✈️ Travel | Groq Llama 3.3 | OpenStreetMap | Itineraries, location lookup, nearby places |
| 🧭 Orchestrator | Gemini 2.5 Flash | — | Intent classification, agent routing |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| UI | Streamlit |
| LLM (Agents) | Groq — Llama 3.3 70B Versatile |
| LLM (Orchestrator + Research) | Google Gemini 2.5 Flash |
| LLM Fallback | Groq ↔ Gemini auto-switch |
| Email | Gmail API (OAuth2) |
| Calendar | Google Calendar API (OAuth2) |
| Search | Tavily API |
| Maps | OpenStreetMap Nominatim + Overpass API |
| Memory | SQLite (conversation history + action logs + error logs) |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-assistant.git
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

---

## 💬 Usage Examples

### Auto-Route Mode
Just type naturally — the orchestrator picks the right agent:
```
"Plan a 5-day trip to Goa on a budget of ₹3000/day"     → Travel Agent
"What are the latest developments in AI in 2025?"         → Research Agent
"Schedule a team standup every Monday at 10am"            → Calendar Agent
"Write a follow-up email to a client who hasn't replied"  → Email Agent
```

### Manual Mode
Click an agent in the sidebar to lock it:
```
/email     → Draft and send real emails via Gmail
/research  → Get live web-searched answers with sources
/calendar  → Create and view real Google Calendar events
/travel    → Build itineraries with real map data
```

---

## 📊 Logs Dashboard

The app has a built-in **Logs Dashboard** tab showing:
- Total actions, success rate, error count, auto-resolved errors
- Actions per agent (bar chart)
- Full action log table with status highlighting
- Error & fallback log — shows which provider failed and whether fallback resolved it

---

## 📁 Project Structure

```
multi_agent_assistant/
  agents/
    email_agent.py        ← Gmail API + Groq
    research_agent.py     ← Tavily search + Gemini
    calendar_agent.py     ← Google Calendar + Groq
    travel_agent.py       ← OpenStreetMap + Groq
  core/
    orchestrator.py       ← Gemini 2.5 Flash routing
    fallback.py           ← Groq → Gemini auto-fallback
    memory.py             ← SQLite (history + logs)
    config.py             ← API clients
  tools/
    gmail_tool.py         ← send/read Gmail
    calendar_tool.py      ← create/list events
    search_tool.py        ← Tavily web search
    maps_tool.py          ← OpenStreetMap lookup
  auth/
    google_auth.py        ← OAuth2 flow
  app.py                  ← Streamlit UI (Chat + Dashboard)
  main.py                 ← CLI entry point
  requirements.txt
  .env.example
```

---

## 🔮 Upcoming Features

- [ ] RAG with ChromaDB for semantic memory search
- [ ] Agent collaboration (cross-agent context passing)
- [ ] Unit tests for routing and agent responses
- [ ] Streamlit Cloud deployment

---

## 📄 License

MIT License — free to use, modify, and share.

---

## 🙋 Author

**Sanchit Yadav**
[LinkedIn](https://linkedin.com/in/sanchit-yadav-b70830266) • [GitHub](https://github.com/sanchit-yadav)
