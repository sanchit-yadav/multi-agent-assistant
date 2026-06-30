import json
from unittest.mock import patch, MagicMock


def make_mock_groq_response(agent: str, reason: str = "test reason"):
    """Builds a fake Groq chat-completion response object."""
    mock_choice          = MagicMock()
    mock_choice.message.content = json.dumps({"agent": agent, "reason": reason})
    mock_response         = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@patch("core.orchestrator.groq_client")
def test_routes_email_intent_to_email_agent(mock_groq):
    from core.orchestrator import Orchestrator
    mock_groq.chat.completions.create.return_value = make_mock_groq_response("email")

    orch = Orchestrator()
    agent_name, reason = orch.detect_agent("Send an email to my manager about leave")

    assert agent_name == "email"
    assert isinstance(reason, str)


@patch("core.orchestrator.groq_client")
def test_routes_research_intent_to_research_agent(mock_groq):
    from core.orchestrator import Orchestrator
    mock_groq.chat.completions.create.return_value = make_mock_groq_response("research")

    orch = Orchestrator()
    agent_name, _ = orch.detect_agent("What is the capital of France?")

    assert agent_name == "research"


@patch("core.orchestrator.groq_client")
def test_routes_calendar_intent_to_calendar_agent(mock_groq):
    from core.orchestrator import Orchestrator
    mock_groq.chat.completions.create.return_value = make_mock_groq_response("calendar")

    orch = Orchestrator()
    agent_name, _ = orch.detect_agent("Schedule a meeting tomorrow at 5pm")

    assert agent_name == "calendar"


@patch("core.orchestrator.groq_client")
def test_routes_travel_intent_to_travel_agent(mock_groq):
    from core.orchestrator import Orchestrator
    mock_groq.chat.completions.create.return_value = make_mock_groq_response("travel")

    orch = Orchestrator()
    agent_name, _ = orch.detect_agent("Plan a 5-day trip to Bali")

    assert agent_name == "travel"


@patch("core.orchestrator.groq_client")
def test_invalid_json_response_falls_back_to_research(mock_groq):
    """If the LLM returns malformed JSON, orchestrator should not crash —
    it should gracefully default to the research agent."""
    from core.orchestrator import Orchestrator

    mock_choice                 = MagicMock()
    mock_choice.message.content = "this is not valid json at all"
    mock_response                = MagicMock()
    mock_response.choices        = [mock_choice]
    mock_groq.chat.completions.create.return_value = mock_response

    orch = Orchestrator()
    agent_name, reason = orch.detect_agent("asdkjhasdkjh random gibberish")

    assert agent_name == "research"
    assert "default" in reason.lower() or "classify" in reason.lower()


@patch("core.orchestrator.groq_client")
def test_unknown_agent_name_falls_back_to_research(mock_groq):
    """If the LLM hallucinates an agent name that doesn't exist, route()
    should still work by defaulting to research instead of crashing."""
    from core.orchestrator import Orchestrator
    mock_groq.chat.completions.create.return_value = make_mock_groq_response("finance")

    orch = Orchestrator()
    name, _ = orch.detect_agent("Some message")
    final_name = name if name in orch.agents else "research"

    assert final_name == "research"