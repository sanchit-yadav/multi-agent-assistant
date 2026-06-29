import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai

load_dotenv()

def get_secret(key: str) -> str:
    # Try Streamlit secrets first (cloud), then .env (local)
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")

if not GEMINI_API_KEY:
    raise ValueError("❌  GEMINI_API_KEY missing in .env")
if not GROQ_API_KEY:
    raise ValueError("❌  GROQ_API_KEY missing in .env")
if not TAVILY_API_KEY:
    raise ValueError("❌  TAVILY_API_KEY missing in .env")

genai.configure(api_key=GEMINI_API_KEY)

# Groq client
try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
except ImportError:
    raise ImportError("❌  groq package not installed. Run: pip install groq")

# Gemini fallback model (used when Groq fails)
GROQ_MODEL   = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.5-flash"