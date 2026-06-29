import sqlite3
import json
from datetime import datetime

DB_PATH = "memory.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS histories (
            agent    TEXT PRIMARY KEY,
            messages TEXT,
            updated  TEXT
        );
        CREATE TABLE IF NOT EXISTS actions_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            agent     TEXT,
            action    TEXT,
            detail    TEXT,
            status    TEXT DEFAULT 'success',
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS error_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            agent     TEXT,
            provider  TEXT,
            error     TEXT,
            fallback  TEXT,
            resolved  INTEGER DEFAULT 0,
            timestamp TEXT
        );
    """)
    # Add status column if upgrading from old DB
    try:
        conn.execute("ALTER TABLE actions_log ADD COLUMN status TEXT DEFAULT 'success'")
        conn.commit()
    except Exception:
        pass
    conn.close()


def save_history(agent: str, history: list):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO histories (agent, messages, updated) VALUES (?, ?, ?)
        ON CONFLICT(agent) DO UPDATE SET
            messages = excluded.messages,
            updated  = excluded.updated
    """, (agent, json.dumps(history), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def load_history(agent: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    row  = conn.execute(
        "SELECT messages FROM histories WHERE agent = ?", (agent,)
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else []


def clear_history(agent: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM histories WHERE agent = ?", (agent,))
    conn.commit()
    conn.close()


def log_action(agent: str, action: str, detail: str, status: str = "success"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO actions_log (agent, action, detail, status, timestamp) VALUES (?, ?, ?, ?, ?)",
        (agent, action, detail, status, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def log_error(agent: str, provider: str, error: str, fallback: str = "", resolved: bool = False):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO error_log (agent, provider, error, fallback, resolved, timestamp) VALUES (?,?,?,?,?,?)",
        (agent, provider, error, fallback, int(resolved), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_action_logs(agent: str = None, limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    if agent and agent != "all":
        rows = conn.execute(
            "SELECT agent, action, detail, status, timestamp FROM actions_log "
            "WHERE agent=? ORDER BY id DESC LIMIT ?",
            (agent, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT agent, action, detail, status, timestamp FROM actions_log "
            "ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [
        {"agent": r[0], "action": r[1], "detail": r[2], "status": r[3], "timestamp": r[4]}
        for r in rows
    ]


def get_error_logs(limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT agent, provider, error, fallback, resolved, timestamp "
        "FROM error_log ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {
            "agent":    r[0], "provider": r[1], "error":    r[2],
            "fallback": r[3], "resolved": bool(r[4]), "timestamp": r[5]
        }
        for r in rows
    ]


def get_stats() -> dict:
    conn  = sqlite3.connect(DB_PATH)
    stats = {}

    # Total actions per agent
    rows = conn.execute(
        "SELECT agent, COUNT(*) FROM actions_log GROUP BY agent"
    ).fetchall()
    stats["actions_per_agent"] = {r[0]: r[1] for r in rows}

    # Success vs failure
    rows = conn.execute(
        "SELECT status, COUNT(*) FROM actions_log GROUP BY status"
    ).fetchall()
    stats["status_counts"] = {r[0]: r[1] for r in rows}

    # Total errors
    stats["total_errors"]    = conn.execute("SELECT COUNT(*) FROM error_log").fetchone()[0]
    stats["resolved_errors"] = conn.execute(
        "SELECT COUNT(*) FROM error_log WHERE resolved=1"
    ).fetchone()[0]

    # Messages per agent
    rows = conn.execute("SELECT agent, messages FROM histories").fetchall()
    stats["messages_per_agent"] = {}
    for r in rows:
        try:
            stats["messages_per_agent"][r[0]] = len(json.loads(r[1]))
        except Exception:
            stats["messages_per_agent"][r[0]] = 0

    conn.close()
    return stats