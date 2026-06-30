def test_save_and_load_history_roundtrip(temp_db):
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    temp_db.save_history("email", history)

    loaded = temp_db.load_history("email")
    assert loaded == history


def test_load_history_returns_empty_list_for_unknown_agent(temp_db):
    loaded = temp_db.load_history("nonexistent_agent")
    assert loaded == []


def test_clear_history_removes_saved_data(temp_db):
    temp_db.save_history("travel", [{"role": "user", "content": "Plan a trip"}])
    assert temp_db.load_history("travel") != []

    temp_db.clear_history("travel")
    assert temp_db.load_history("travel") == []


def test_log_action_and_retrieve(temp_db):
    temp_db.log_action("calendar", "create_event", "Team sync on 2025-07-01", "success")

    logs = temp_db.get_action_logs(agent="calendar", limit=10)
    assert len(logs) == 1
    assert logs[0]["action"] == "create_event"
    assert logs[0]["status"] == "success"