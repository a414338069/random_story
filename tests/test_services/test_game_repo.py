"""Tests for game_repo serialization/deserialization roundtrip."""

import os
import tempfile

from app.database import get_db, init_db
from app.repositories.game_repo import (
    save_player,
    load_player,
    _state_to_db_row,
    _db_row_to_state,
)


def _new_db():
    """Create a fresh in-memory database with current schema."""
    db_path = os.path.join(tempfile.gettempdir(), "test_game_repo.db")
    conn = get_db(db_path)
    init_db(conn)
    return conn, db_path


class TestStateRoundtrip:
    """Verify state dict survives save → load cycle with all new fields."""

    def test_state_roundtrip_with_new_fields(self):
        """Save state with cultivation=45.5, age=25, technique_grades, ascended=True."""
        conn, db_path = _new_db()
        try:
            state = {
                "session_id": "test-roundtrip-001",
                "name": "测试修士",
                "gender": "男",
                "attributes": {
                    "rootBone": 3,
                    "comprehension": 3,
                    "mindset": 2,
                    "luck": 2,
                },
                "talent_ids": ["f01"],
                "realm": "炼气",
                "realm_progress": 0.5,
                "health": 90.0,
                "qi": 10.0,
                "lifespan": 120,
                "faction": "青云门",
                "spirit_stones": 100,
                "techniques": ["tech_001"],
                "inventory": ["item_001"],
                "event_count": 5,
                "score": 42,
                "ending_id": "寿终正寝",
                "is_alive": True,
                "user_id": "user-abc",
                "save_slot": 1,
                "age": 25,
                "cultivation": 45.5,
                "ascended": True,
                "technique_grades": ["灵品", "玄品"],
                "_pending_breakthrough": True,
                "_breakthrough_next_req": 200.0,
            }

            save_player(conn, state)
            conn.commit()

            loaded = load_player(conn, "test-roundtrip-001")
            assert loaded is not None

            # Verify all standard fields roundtrip
            assert loaded["session_id"] == "test-roundtrip-001"
            assert loaded["name"] == "测试修士"
            assert loaded["gender"] == "男"
            assert loaded["realm"] == "炼气"
            assert loaded["realm_progress"] == 0.5
            assert loaded["health"] == 90.0
            assert loaded["qi"] == 10.0
            assert loaded["lifespan"] == 120
            assert loaded["faction"] == "青云门"
            assert loaded["spirit_stones"] == 100
            assert loaded["techniques"] == ["tech_001"]
            assert loaded["inventory"] == ["item_001"]
            assert loaded["event_count"] == 5
            assert loaded["score"] == 42
            assert loaded["ending_id"] == "寿终正寝"
            assert loaded["is_alive"] is True
            assert loaded["talent_ids"] == ["f01"]

            # Verify new fields roundtrip
            assert loaded["user_id"] == "user-abc"
            assert loaded["save_slot"] == 1
            assert loaded["age"] == 25
            assert loaded["cultivation"] == 45.5
            assert loaded["ascended"] is True
            assert loaded["technique_grades"] == ["灵品", "玄品"]
            assert loaded["_pending_breakthrough"] is True
            assert loaded["_breakthrough_next_req"] == 200.0

            # Verify attributes
            attrs = loaded["attributes"]
            assert attrs["rootBone"] == 3
            assert attrs["comprehension"] == 3
            assert attrs["mindset"] == 2
            assert attrs["luck"] == 2
        finally:
            conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_state_roundtrip_defaults(self):
        """State with minimal fields (defaults) survives roundtrip correctly."""
        conn, db_path = _new_db()
        try:
            state = {
                "session_id": "test-roundtrip-defaults",
                "name": "默认修士",
                "gender": "女",
                "attributes": {
                    "rootBone": 0,
                    "comprehension": 0,
                    "mindset": 0,
                    "luck": 0,
                },
                "talent_ids": [],
                "techniques": [],
                "inventory": [],
            }

            save_player(conn, state)
            conn.commit()

            loaded = load_player(conn, "test-roundtrip-defaults")
            assert loaded is not None

            # New fields should have their defaults
            assert loaded["age"] == 0
            assert loaded["cultivation"] == 0.0
            assert loaded["ascended"] is False
            assert loaded["technique_grades"] == []
            assert loaded["_pending_breakthrough"] is False
            assert loaded["_breakthrough_next_req"] == 0.0
            assert loaded["user_id"] is None
            assert loaded["save_slot"] == 0
        finally:
            conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_state_roundtrip_none_user_id(self):
        """user_id=None survives roundtrip (backward compat for old records)."""
        conn, db_path = _new_db()
        try:
            state = {
                "session_id": "test-roundtrip-none-uid",
                "name": "古早修士",
                "gender": "男",
                "attributes": {
                    "rootBone": 0,
                    "comprehension": 0,
                    "mindset": 0,
                    "luck": 0,
                },
                "talent_ids": [],
                "techniques": [],
                "inventory": [],
                "user_id": None,
            }

            save_player(conn, state)
            conn.commit()

            loaded = load_player(conn, "test-roundtrip-none-uid")
            assert loaded is not None
            assert loaded["user_id"] is None
        finally:
            conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)
