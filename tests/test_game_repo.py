import json

import pytest

from app.database import get_db, init_db
from app.repositories.game_repo import (
    save_player,
    load_player,
    delete_player,
    save_event_log,
    get_leaderboard,
)


@pytest.fixture
def db():
    conn = get_db(":memory:")
    init_db(conn)
    yield conn
    conn.close()


_SAMPLE_STATE = {
    "session_id": "abc123",
    "name": "叶凡",
    "gender": "男",
    "attributes": {
        "rootBone": 5,
        "comprehension": 3,
        "mindset": 1,
        "luck": 1,
    },
    "talent_ids": ["talent_blade", "talent_pill"],
    "realm": "练气",
    "realm_progress": 0.3,
    "spirit_stones": 42,
    "lifespan": 100,
    "faction": "散修",
    "techniques": [
        "基础剑法",
        {"name": "御风术", "grade": "灵品"},
    ],
    "inventory": [
        {"id": "herb_1", "name": "聚气草", "quantity": 3},
    ],
    "is_alive": True,
    "event_count": 5,
    "score": 0,
    "cultivation": 150.0,
    "age": 18,
    "technique_grades": ["凡品", "灵品"],
    "ascended": False,
}


class TestSaveLoadRoundtrip:
    def test_roundtrip_preserves_scalar_fields(self, db):
        save_player(db, _SAMPLE_STATE)
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded is not None
        assert loaded["session_id"] == "abc123"
        assert loaded["name"] == "叶凡"
        assert loaded["gender"] == "男"
        assert loaded["realm"] == "练气"
        assert loaded["realm_progress"] == pytest.approx(0.3)
        assert loaded["spirit_stones"] == 42
        assert loaded["lifespan"] == 100
        assert loaded["faction"] == "散修"
        assert loaded["is_alive"] is True
        assert loaded["event_count"] == 5
        assert loaded["score"] == 0

    def test_roundtrip_preserves_attributes_dict(self, db):
        save_player(db, _SAMPLE_STATE)
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded["attributes"] == {
            "rootBone": 5,
            "comprehension": 3,
            "mindset": 1,
            "luck": 1,
        }

    def test_roundtrip_json_fields(self, db):
        save_player(db, _SAMPLE_STATE)
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded["talent_ids"] == ["talent_blade", "talent_pill"]
        assert loaded["techniques"] == [
            "基础剑法",
            {"name": "御风术", "grade": "灵品"},
        ]
        assert loaded["inventory"] == [
            {"id": "herb_1", "name": "聚气草", "quantity": 3},
        ]

    def test_roundtrip_defaults_for_non_db_fields(self, db):
        save_player(db, _SAMPLE_STATE)
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded["age"] == 0
        assert loaded["cultivation"] == 0.0
        assert loaded["technique_grades"] == []
        assert loaded["ascended"] is False

    def test_insert_or_replace_updates_existing(self, db):
        save_player(db, _SAMPLE_STATE)
        db.commit()

        updated = dict(_SAMPLE_STATE)
        updated["realm"] = "筑基"
        updated["spirit_stones"] = 999
        updated["talent_ids"] = ["talent_new"]
        save_player(db, updated)
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded["realm"] == "筑基"
        assert loaded["spirit_stones"] == 999
        assert loaded["talent_ids"] == ["talent_new"]

    def test_needs_explicit_commit(self, db):
        save_player(db, _SAMPLE_STATE)

        conn2 = get_db(":memory:")
        init_db(conn2)
        loaded = load_player(conn2, "abc123")
        assert loaded is None
        conn2.close()

    def test_empty_lists_for_json_columns(self, db):
        state = dict(_SAMPLE_STATE)
        state["talent_ids"] = []
        state["techniques"] = []
        state["inventory"] = []
        save_player(db, state)
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded["talent_ids"] == []
        assert loaded["techniques"] == []
        assert loaded["inventory"] == []


class TestLoadMissing:
    def test_returns_none_for_unknown_session(self, db):
        result = load_player(db, "nonexistent")
        assert result is None


class TestDelete:
    def test_delete_removes_player(self, db):
        save_player(db, _SAMPLE_STATE)
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded is not None

        delete_player(db, "abc123")
        db.commit()

        loaded = load_player(db, "abc123")
        assert loaded is None

    def test_delete_nonexistent_is_noop(self, db):
        delete_player(db, "nonexistent")


class TestEventLog:
    def test_saves_event_log(self, db):
        save_player(db, _SAMPLE_STATE)
        db.commit()

        event = {
            "event_index": 1,
            "event_type": "adventure",
            "narrative": "你发现了一处秘境入口。",
            "options": [{"id": "enter", "text": "进入探索"}],
            "chosen_option_id": "enter",
            "consequences": {"qi": 10, "spirit_stones_gain": 5},
        }
        save_event_log(db, "abc123", event)
        db.commit()

        row = db.execute(
            "SELECT * FROM event_logs WHERE player_id = ?", ("abc123",)
        ).fetchone()
        assert row is not None
        assert row["player_id"] == "abc123"
        assert row["event_index"] == 1
        assert row["event_type"] == "adventure"
        assert row["narrative"] == "你发现了一处秘境入口。"
        assert json.loads(row["options"]) == [
            {"id": "enter", "text": "进入探索"}
        ]
        assert row["chosen_option_id"] == "enter"
        assert json.loads(row["consequences"]) == {
            "qi": 10,
            "spirit_stones_gain": 5,
        }

    def test_event_log_foreign_key_enforced(self, db):
        with pytest.raises(Exception):
            save_event_log(db, "nonexistent", {"event_index": 0})


class TestLeaderboard:
    def test_returns_completed_games_only(self, db):
        alive = dict(_SAMPLE_STATE)
        alive["session_id"] = "alive_player"
        alive["name"] = "活着的"
        alive["score"] = 100
        alive["is_alive"] = True

        dead1 = dict(_SAMPLE_STATE)
        dead1["session_id"] = "dead_player_1"
        dead1["name"] = "死者一"
        dead1["score"] = 200
        dead1["is_alive"] = False

        dead2 = dict(_SAMPLE_STATE)
        dead2["session_id"] = "dead_player_2"
        dead2["name"] = "死者二"
        dead2["score"] = 150
        dead2["is_alive"] = False

        save_player(db, alive)
        save_player(db, dead1)
        save_player(db, dead2)
        db.commit()

        board = get_leaderboard(db, limit=10)
        assert len(board) == 2
        assert board[0]["name"] == "死者一"
        assert board[0]["score"] == 200
        assert board[1]["name"] == "死者二"
        assert board[1]["score"] == 150
        assert all(entry["name"] != "活着的" for entry in board)

    def test_respects_limit(self, db):
        for i in range(5):
            state = dict(_SAMPLE_STATE)
            state["session_id"] = f"dead_{i}"
            state["is_alive"] = False
            state["score"] = i * 10
            save_player(db, state)
        db.commit()

        board = get_leaderboard(db, limit=3)
        assert len(board) == 3

    def test_empty_when_no_completed_games(self, db):
        board = get_leaderboard(db)
        assert board == []
