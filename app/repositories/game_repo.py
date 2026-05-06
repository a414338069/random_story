"""SQLite repository layer for game state persistence.

Maps the in-memory state dict (used by game_service) to the ``players`` and
``event_logs`` tables defined in schema.sql.  List/dict fields are serialised
as JSON TEXT columns.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.database import get_db

_JSON_COLUMNS = frozenset({"talent_ids", "techniques", "inventory"})


def _serialise_json_fields(row: dict) -> dict:
    for col in _JSON_COLUMNS:
        if col in row and not isinstance(row[col], str):
            row[col] = json.dumps(row[col], ensure_ascii=False)
    return row


def _deserialise_json_fields(row: dict) -> dict:
    for col in _JSON_COLUMNS:
        if col in row and isinstance(row[col], str):
            try:
                row[col] = json.loads(row[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return row


def _state_to_db_row(state: dict) -> dict:
    """Flatten a game_service state dict into a row for the ``players`` table."""
    attrs = state.get("attributes", {})

    return {
        "id": state["session_id"],
        "name": state.get("name", ""),
        "gender": state.get("gender", ""),
        "root_bone": attrs.get("rootBone", 0) or attrs.get("root_bone", 0),
        "comprehension": attrs.get("comprehension", 0),
        "mindset": attrs.get("mindset", 0),
        "luck": attrs.get("luck", 0),
        "realm": state.get("realm", ""),
        "realm_progress": state.get("realm_progress", 0.0),
        "health": state.get("health", 100.0),
        "qi": state.get("qi", 0.0),
        "lifespan": state.get("lifespan", 0),
        "faction": state.get("faction", ""),
        "spirit_stones": state.get("spirit_stones", 0),
        "talent_ids": list(state.get("talent_ids", [])),
        "techniques": list(state.get("techniques", [])),
        "inventory": list(state.get("inventory", [])),
        "event_count": state.get("event_count", 0),
        "score": state.get("score", 0),
        "ending_id": state.get("ending_id"),
        "is_alive": 1 if state.get("is_alive", True) else 0,
        "last_active_at": datetime.now(timezone.utc).isoformat(),
    }


def _db_row_to_state(row: sqlite3.Row) -> dict:
    """Build a state dict from a ``players`` table row, restoring defaults
    for fields that have no corresponding DB column."""
    d = dict(row)
    d = _deserialise_json_fields(d)

    for col in _JSON_COLUMNS:
        if not isinstance(d.get(col), list):
            d[col] = []

    return {
        "session_id": d["id"],
        "name": d.get("name", ""),
        "gender": d.get("gender", ""),
        "attributes": {
            "rootBone": d.get("root_bone", 0),
            "comprehension": d.get("comprehension", 0),
            "mindset": d.get("mindset", 0),
            "luck": d.get("luck", 0),
        },
        "talent_ids": d["talent_ids"],
        "realm": d.get("realm", ""),
        "realm_progress": d.get("realm_progress", 0.0),
        "health": d.get("health", 100.0),
        "qi": d.get("qi", 0.0),
        "lifespan": d.get("lifespan", 0),
        "faction": d.get("faction", ""),
        "spirit_stones": d.get("spirit_stones", 0),
        "techniques": d["techniques"],
        "inventory": d["inventory"],
        "event_count": d.get("event_count", 0),
        "score": d.get("score", 0),
        "ending_id": d.get("ending_id"),
        "is_alive": bool(d.get("is_alive", 1)),
        "age": 0,
        "cultivation": 0.0,
        "technique_grades": [],
        "ascended": False,
    }


def save_player(conn: sqlite3.Connection, state: dict) -> None:
    """INSERT OR REPLACE the game state into the ``players`` table."""
    row = _state_to_db_row(state)
    row = _serialise_json_fields(row)

    columns = list(row.keys())
    placeholders = ", ".join(":" + c for c in columns)
    sql = (
        f"INSERT OR REPLACE INTO players ({', '.join(columns)}) "
        f"VALUES ({placeholders})"
    )
    conn.execute(sql, row)


def load_player(
    conn: sqlite3.Connection, session_id: str
) -> dict | None:
    """Load game state from the ``players`` table, or None if not found."""
    row = conn.execute(
        "SELECT * FROM players WHERE id = ?", (session_id,)
    ).fetchone()
    if row is None:
        return None
    return _db_row_to_state(row)


def delete_player(conn: sqlite3.Connection, session_id: str) -> None:
    """DELETE a player row from the ``players`` table."""
    conn.execute("DELETE FROM players WHERE id = ?", (session_id,))


def save_event_log(
    conn: sqlite3.Connection, session_id: str, event_data: dict
) -> None:
    """INSERT an event record into the ``event_logs`` table."""
    row = {
        "player_id": session_id,
        "event_index": event_data.get("event_index", 0),
        "event_type": event_data.get("event_type", ""),
        "narrative": event_data.get("narrative", ""),
        "options": event_data.get("options", []),
        "chosen_option_id": event_data.get("chosen_option_id"),
        "consequences": event_data.get("consequences", {}),
    }

    if not isinstance(row["options"], str):
        row["options"] = json.dumps(row["options"], ensure_ascii=False)
    if not isinstance(row["consequences"], str):
        row["consequences"] = json.dumps(
            row["consequences"], ensure_ascii=False
        )

    columns = list(row.keys())
    placeholders = ", ".join(":" + c for c in columns)
    sql = (
        f"INSERT INTO event_logs ({', '.join(columns)}) "
        f"VALUES ({placeholders})"
    )
    conn.execute(sql, row)


def get_recent_event_summaries(
    conn: sqlite3.Connection, session_id: str, limit: int = 5
) -> list[dict]:
    """Fetch the most recent event log entries for AI context."""
    rows = conn.execute(
        """SELECT event_index, event_type, narrative, chosen_option_id, consequences
           FROM event_logs
           WHERE player_id = ?
           ORDER BY event_index DESC
           LIMIT ?""",
        (session_id, limit),
    ).fetchall()
    result = []
    for row in rows:
        entry = dict(row)
        if isinstance(entry.get("consequences"), str):
            try:
                entry["consequences"] = json.loads(entry["consequences"])
            except (json.JSONDecodeError, TypeError):
                pass
        result.append(entry)
    return result


def get_leaderboard(
    conn: sqlite3.Connection, limit: int = 10
) -> list[dict]:
    """Top *limit* scores from completed games (is_alive = 0)."""
    rows = conn.execute(
        "SELECT id, name, realm, score "
        "FROM players "
        "WHERE is_alive = 0 "
        "ORDER BY score DESC "
        "LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
