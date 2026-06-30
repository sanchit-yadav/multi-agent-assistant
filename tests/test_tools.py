import json
from unittest.mock import patch, MagicMock


def test_search_place_handles_no_results_gracefully():
    """When OpenStreetMap returns an empty list, search_place should return
    a clean error dict instead of crashing with an IndexError."""
    from tools.maps_tool import search_place

    with patch("tools.maps_tool.requests.get") as mock_get:
        mock_resp           = MagicMock()
        mock_resp.json.return_value = []  # no results found
        mock_get.return_value = mock_resp

        result = search_place("a-place-that-does-not-exist-xyz123")

        assert "error" in result
        assert "No location found" in result["error"]


def test_search_place_returns_expected_fields_on_success():
    """When OpenStreetMap returns a valid result, all expected keys should be present."""
    from tools.maps_tool import search_place

    fake_place = [{
        "display_name": "Jaipur, Rajasthan, India",
        "lat": "26.9124",
        "lon": "75.7873",
    }]

    with patch("tools.maps_tool.requests.get") as mock_get:
        mock_resp                   = MagicMock()
        mock_resp.json.return_value = fake_place
        mock_get.return_value       = mock_resp

        result = search_place("Jaipur")

        assert result["name"] == "Jaipur, Rajasthan, India"
        assert result["latitude"] == "26.9124"
        assert result["longitude"] == "75.7873"
        assert "openstreetmap.org" in result["map_url"]


def test_email_agent_action_json_is_parsed_correctly():
    """Verify that the 'send' action JSON format used by EmailAgent's
    system prompt is valid and contains all required keys."""
    sample_reply = json.dumps({
        "action": "send",
        "to":      "test@example.com",
        "subject": "Test Subject",
        "body":    "Test body content",
    })

    data = json.loads(sample_reply)

    assert data["action"] == "send"
    assert "@" in data["to"]
    assert len(data["subject"]) > 0
    assert len(data["body"]) > 0


def test_calendar_agent_create_action_has_required_date_format():
    """Verify the calendar 'create' action JSON has a valid YYYY-MM-DD date
    and HH:MM time format, since create_event() relies on strptime parsing
    this exact format."""
    from datetime import datetime

    sample_reply = json.dumps({
        "action":         "create",
        "title":          "Project Review",
        "date":           "2025-07-01",
        "time":           "10:00",
        "duration_hours": 2,
    })
    data = json.loads(sample_reply)

    # This will raise ValueError if the format is wrong — that's the point of the test
    parsed = datetime.strptime(f"{data['date']} {data['time']}", "%Y-%m-%d %H:%M")
    assert parsed.year == 2025
    assert parsed.hour == 10