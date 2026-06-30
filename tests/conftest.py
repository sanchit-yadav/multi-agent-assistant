import os
import sys
import pytest

# ── Dummy env vars so core/config.py doesn't crash on import ──────────────────
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Ensure dummy keys are present for every test, even if something clears them."""
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    yield


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Provide a temporary, isolated SQLite DB for memory tests."""
    import core.memory as memory_module
    db_path = str(tmp_path / "test_memory.db")
    monkeypatch.setattr(memory_module, "DB_PATH", db_path)
    memory_module.init_db()
    return memory_module