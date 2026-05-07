"""Tests for database layer — schema creation and CRUD operations."""
import json
import sqlite3

import pytest

from app.database import get_db, init_db


@pytest.fixture
def db():
    """Provide an in-memory database initialized with schema."""
    conn = get_db(":memory:")
    init_db(conn)
    yield conn
    conn.close()


class TestInitDB:
    """Verify init_db() creates the expected tables."""

    def test_creates_all_four_tables(self):
        conn = get_db(":memory:")
        init_db(conn)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert tables == ["ai_cache", "event_logs", "event_templates", "players"]
        conn.close()

    def test_is_idempotent(self):
        """Running init_db twice must not raise (due to IF NOT EXISTS)."""
        conn = get_db(":memory:")
        init_db(conn)
        init_db(conn)
        cursor = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
        assert cursor.fetchone()[0] == 4
        conn.close()


class TestPlayersTable:
    """Schema validation + CRUD for players."""

    SCHEMA_EXPECTED = {
        "id": "TEXT",
        "name": "TEXT",
        "gender": "TEXT",
        "talent_ids": "TEXT",
        "root_bone": "INTEGER",
        "comprehension": "INTEGER",
        "mindset": "INTEGER",
        "luck": "INTEGER",
        "realm": "TEXT",
        "realm_progress": "REAL",
        "health": "REAL",
        "qi": "REAL",
        "lifespan": "INTEGER",
        "faction": "TEXT",
        "spirit_stones": "INTEGER",
        "techniques": "TEXT",
        "inventory": "TEXT",
        "event_count": "INTEGER",
        "score": "INTEGER",
        "ending_id": "TEXT",
        "is_alive": "INTEGER",
        "last_active_at": "TIMESTAMP",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    }

    def test_schema_columns(self, db):
        cursor = db.execute("PRAGMA table_info(players)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}
        for col_name, col_type in self.SCHEMA_EXPECTED.items():
            assert col_name in columns, f"Missing column: {col_name}"
            assert columns[col_name] == col_type, (
                f"Column {col_name}: expected {col_type}, got {columns[col_name]}"
            )

    def test_pk_is_id(self, db):
        cursor = db.execute("PRAGMA table_info(players)")
        pk_cols = [row["name"] for row in cursor.fetchall() if row["pk"] == 1]
        assert pk_cols == ["id"]

    def test_crud(self, db):
        player_id = "test-player-1"

        db.execute(
            """INSERT INTO players
               (id, name, gender, talent_ids, root_bone, comprehension,
                mindset, luck, realm, realm_progress, health, qi, lifespan,
                faction, spirit_stones, techniques, inventory, event_count,
                score, ending_id, is_alive, last_active_at,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'),
                       datetime('now'), datetime('now'))""",
            (
                player_id,
                "测试角色",
                "男",
                json.dumps(["talent_1", "talent_2"]),
                50,
                60,
                70,
                30,
                "炼气",
                0.5,
                100.0,
                50.0,
                100,
                "散修",
                0,
                json.dumps([]),
                json.dumps([]),
                0,
                0,
                None,
                1,
            ),
        )

        row = db.execute(
            "SELECT * FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        assert row is not None
        assert row["name"] == "测试角色"
        assert row["gender"] == "男"
        assert json.loads(row["talent_ids"]) == ["talent_1", "talent_2"]
        assert row["root_bone"] == 50
        assert row["comprehension"] == 60
        assert row["mindset"] == 70
        assert row["luck"] == 30
        assert row["realm"] == "炼气"
        assert row["realm_progress"] == 0.5
        assert row["health"] == 100.0
        assert row["qi"] == 50.0
        assert row["lifespan"] == 100
        assert row["faction"] == "散修"
        assert row["spirit_stones"] == 0
        assert json.loads(row["techniques"]) == []
        assert json.loads(row["inventory"]) == []
        assert row["event_count"] == 0
        assert row["score"] == 0
        assert row["ending_id"] is None
        assert row["is_alive"] == 1

        db.execute(
            "UPDATE players SET health = ?, event_count = ? WHERE id = ?",
            (80.0, 1, player_id),
        )
        db.commit()
        row = db.execute(
            "SELECT health, event_count FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        assert row["health"] == 80.0
        assert row["event_count"] == 1

        db.execute("DELETE FROM players WHERE id = ?", (player_id,))
        db.commit()
        row = db.execute(
            "SELECT * FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        assert row is None


class TestEventLogsTable:
    """Schema validation + CRUD for event_logs."""

    SCHEMA_EXPECTED = {
        "id": "INTEGER",
        "player_id": "TEXT",
        "event_index": "INTEGER",
        "event_type": "TEXT",
        "narrative": "TEXT",
        "options": "TEXT",
        "chosen_option_id": "TEXT",
        "consequences": "TEXT",
        "created_at": "TIMESTAMP",
    }

    def test_schema_columns(self, db):
        cursor = db.execute("PRAGMA table_info(event_logs)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}
        for col_name, col_type in self.SCHEMA_EXPECTED.items():
            assert col_name in columns, f"Missing column: {col_name}"
            assert columns[col_name] == col_type

    def test_pk_is_autoincrement_id(self, db):
        cursor = db.execute("PRAGMA table_info(event_logs)")
        pk_cols = {row["name"]: row for row in cursor.fetchall() if row["pk"] == 1}
        assert list(pk_cols.keys()) == ["id"]

    def test_foreign_key_to_players(self, db):
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO event_logs (player_id, event_index, event_type) "
                "VALUES ('non-existent', 1, 'test')"
            )

    def test_crud(self, db):
        db.execute(
            "INSERT INTO players (id, name, created_at, updated_at) "
            "VALUES (?, ?, datetime('now'), datetime('now'))",
            ("player-1", "测试角色"),
        )

        db.execute(
            "INSERT INTO event_logs "
            "(player_id, event_index, event_type, narrative, options, "
            " chosen_option_id, consequences, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (
                "player-1",
                1,
                "test_event",
                "一段叙事文本",
                json.dumps([{"id": "opt_1", "text": "选项A"}]),
                "opt_1",
                json.dumps({"hp": -10, "qi": 5}),
            ),
        )

        rows = db.execute(
            "SELECT * FROM event_logs WHERE player_id = ? ORDER BY event_index",
            ("player-1",),
        ).fetchall()
        assert len(rows) >= 1
        row = rows[0]
        assert row["event_index"] == 1
        assert row["event_type"] == "test_event"
        assert row["narrative"] == "一段叙事文本"
        assert json.loads(row["options"]) == [{"id": "opt_1", "text": "选项A"}]
        assert row["chosen_option_id"] == "opt_1"
        assert json.loads(row["consequences"]) == {"hp": -10, "qi": 5}

        db.execute(
            "UPDATE event_logs SET chosen_option_id = ? WHERE id = ?",
            ("opt_2", row["id"]),
        )
        db.commit()
        updated = db.execute(
            "SELECT chosen_option_id FROM event_logs WHERE id = ?", (row["id"],)
        ).fetchone()
        assert updated["chosen_option_id"] == "opt_2"


class TestAiCacheTable:
    """Schema validation + CRUD for ai_cache."""

    SCHEMA_EXPECTED = {
        "id": "INTEGER",
        "cache_key": "TEXT",
        "response": "TEXT",
        "hit_count": "INTEGER",
        "created_at": "TIMESTAMP",
    }

    def test_schema_columns(self, db):
        cursor = db.execute("PRAGMA table_info(ai_cache)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}
        for col_name, col_type in self.SCHEMA_EXPECTED.items():
            assert col_name in columns, f"Missing column: {col_name}"
            assert columns[col_name] == col_type

    def test_cache_key_unique_constraint(self, db):
        db.execute(
            "INSERT INTO ai_cache (cache_key, response) VALUES (?, ?)",
            ("key_1", json.dumps({"result": "data"})),
        )
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            db.execute(
                "INSERT INTO ai_cache (cache_key, response) VALUES (?, ?)",
                ("key_1", json.dumps({"result": "duplicate"})),
            )

    def test_hit_count_default(self, db):
        db.execute(
            "INSERT INTO ai_cache (cache_key, response) VALUES (?, ?)",
            ("key_default", json.dumps({"msg": "hello"})),
        )
        row = db.execute(
            "SELECT hit_count FROM ai_cache WHERE cache_key = ?", ("key_default",)
        ).fetchone()
        assert row["hit_count"] == 1, "hit_count should default to 1"

    def test_crud(self, db):
        db.execute(
            "INSERT INTO ai_cache (cache_key, response, hit_count, created_at) "
            "VALUES (?, ?, ?, datetime('now'))",
            ("test_key", json.dumps({"answer": 42}), 5),
        )

        row = db.execute(
            "SELECT * FROM ai_cache WHERE cache_key = ?", ("test_key",)
        ).fetchone()
        assert row is not None
        assert json.loads(row["response"]) == {"answer": 42}
        assert row["hit_count"] == 5

        db.execute(
            "UPDATE ai_cache SET hit_count = hit_count + 1 WHERE cache_key = ?",
            ("test_key",),
        )
        db.commit()
        row = db.execute(
            "SELECT hit_count FROM ai_cache WHERE cache_key = ?", ("test_key",)
        ).fetchone()
        assert row["hit_count"] == 6

        db.execute("DELETE FROM ai_cache WHERE cache_key = ?", ("test_key",))
        db.commit()
        row = db.execute(
            "SELECT * FROM ai_cache WHERE cache_key = ?", ("test_key",)
        ).fetchone()
        assert row is None


class TestEventTemplatesTable:
    """Schema validation + CRUD for event_templates."""

    SCHEMA_EXPECTED = {
        "id": "TEXT",
        "type": "TEXT",
        "name": "TEXT",
        "min_realm": "TEXT",
        "max_realm": "TEXT",
        "weight": "REAL",
        "prompt_template": "TEXT",
        "fallback_narrative": "TEXT",
        "default_options": "TEXT",
        "is_active": "INTEGER",
    }

    def test_schema_columns(self, db):
        cursor = db.execute("PRAGMA table_info(event_templates)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}
        for col_name, col_type in self.SCHEMA_EXPECTED.items():
            assert col_name in columns, f"Missing column: {col_name}"
            assert columns[col_name] == col_type

    def test_pk_is_id(self, db):
        cursor = db.execute("PRAGMA table_info(event_templates)")
        pk_cols = [row["name"] for row in cursor.fetchall() if row["pk"] == 1]
        assert pk_cols == ["id"]

    def test_crud(self, db):
        template_id = "evt_breakthrough"

        db.execute(
            "INSERT INTO event_templates "
            "(id, type, name, min_realm, max_realm, weight, "
            " prompt_template, fallback_narrative, default_options, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                template_id,
                "cultivation",
                "突破瓶颈",
                "炼气",
                "金丹",
                1.0,
                "玩家正在尝试突破，描述这个过程。",
                "你感到体内灵气涌动，尝试突破瓶颈。",
                json.dumps([{"id": "focus", "text": "集中全力突破"}]),
                1,
            ),
        )

        row = db.execute(
            "SELECT * FROM event_templates WHERE id = ?", (template_id,)
        ).fetchone()
        assert row is not None
        assert row["type"] == "cultivation"
        assert row["name"] == "突破瓶颈"
        assert row["min_realm"] == "炼气"
        assert row["max_realm"] == "金丹"
        assert row["weight"] == 1.0
        assert "正在尝试突破" in row["prompt_template"]
        assert "灵气涌动" in row["fallback_narrative"]
        assert json.loads(row["default_options"]) == [
            {"id": "focus", "text": "集中全力突破"}
        ]
        assert row["is_active"] == 1

        db.execute(
            "UPDATE event_templates SET weight = ?, is_active = ? WHERE id = ?",
            (2.5, 0, template_id),
        )
        db.commit()
        row = db.execute(
            "SELECT weight, is_active FROM event_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        assert row["weight"] == 2.5
        assert row["is_active"] == 0
