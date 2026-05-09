"""Tests for DB migration (PRAGMA user_version based schema upgrade)."""

import os
import tempfile

from app.database import get_db, init_db

# Old schema WITHOUT the 8 new columns (exactly as it was before Task 1)
_OLD_SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL DEFAULT '',
    gender          TEXT NOT NULL DEFAULT '',
    talent_ids      TEXT NOT NULL DEFAULT '[]',
    root_bone       INTEGER NOT NULL DEFAULT 0,
    comprehension   INTEGER NOT NULL DEFAULT 0,
    mindset         INTEGER NOT NULL DEFAULT 0,
    luck            INTEGER NOT NULL DEFAULT 0,
    realm           TEXT NOT NULL DEFAULT '',
    realm_progress  REAL NOT NULL DEFAULT 0.0,
    health          REAL NOT NULL DEFAULT 100.0,
    qi              REAL NOT NULL DEFAULT 0.0,
    lifespan        INTEGER NOT NULL DEFAULT 100,
    faction         TEXT NOT NULL DEFAULT '',
    spirit_stones   INTEGER NOT NULL DEFAULT 0,
    techniques      TEXT NOT NULL DEFAULT '[]',
    inventory       TEXT NOT NULL DEFAULT '[]',
    event_count     INTEGER NOT NULL DEFAULT 0,
    score           INTEGER NOT NULL DEFAULT 0,
    ending_id       TEXT,
    is_alive        INTEGER NOT NULL DEFAULT 1,
    last_active_at  TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

_NEW_COLUMNS = {
    "user_id", "save_slot", "age", "cultivation",
    "ascended", "technique_grades",
    "_pending_breakthrough", "_breakthrough_next_req",
}


class TestDBMigration:
    """Verify init_db() applies schema migrations for existing databases."""

    def test_migration_adds_new_columns(self):
        """Create an old-schema DB, run init_db, verify new columns exist."""
        db_path = os.path.join(tempfile.gettempdir(), "test_migration_cols.db")
        try:
            # Create old-schema database
            conn = get_db(db_path)
            conn.executescript(_OLD_SCHEMA)
            conn.commit()
            conn.close()

            # Verify old columns are missing before migration
            conn = get_db(db_path)
            old_cols = {
                r[1] for r in conn.execute("PRAGMA table_info(players)")
            }
            for col in _NEW_COLUMNS:
                assert col not in old_cols, f"{col} should not exist before migration"
            conn.close()

            # Run migration
            conn = get_db(db_path)
            init_db(conn)

            # Verify new columns now exist
            new_cols = {
                r[1] for r in conn.execute("PRAGMA table_info(players)")
            }
            for col in _NEW_COLUMNS:
                assert col in new_cols, f"{col} should exist after migration"
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_migration_sets_user_version(self):
        """Verify PRAGMA user_version = 1 after migration."""
        db_path = os.path.join(tempfile.gettempdir(), "test_migration_ver.db")
        try:
            # Create old-schema database
            conn = get_db(db_path)
            conn.executescript(_OLD_SCHEMA)
            conn.commit()
            conn.close()

            # Verify version is 0 before migration
            conn = get_db(db_path)
            v_before = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v_before == 0
            conn.close()

            # Run migration
            conn = get_db(db_path)
            init_db(conn)

            v_after = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v_after == 3
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_migration_idempotent(self):
        """Running init_db twice on same DB does not fail or duplicate."""
        db_path = os.path.join(tempfile.gettempdir(), "test_migration_idem.db")
        try:
            # Create old-schema database
            conn = get_db(db_path)
            conn.executescript(_OLD_SCHEMA)
            conn.commit()
            conn.close()

            # First migration
            conn = get_db(db_path)
            init_db(conn)
            conn.close()

            # Second migration - should be a no-op
            conn = get_db(db_path)
            init_db(conn)
            v = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v == 3
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_new_db_has_all_columns(self):
        """Brand new database (no existing file) gets all columns from schema.sql."""
        db_path = os.path.join(tempfile.gettempdir(), "test_migration_new.db")
        try:
            conn = get_db(db_path)
            init_db(conn)

            cols = {
                r[1] for r in conn.execute("PRAGMA table_info(players)")
            }
            for col in _NEW_COLUMNS:
                assert col in cols, f"{col} should exist in new DB"

            v = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v == 3
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


# Old event_logs schema WITHOUT realm and aftermath columns
_OLD_EVENT_LOGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS event_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       TEXT NOT NULL REFERENCES players(id),
    event_index     INTEGER NOT NULL DEFAULT 0,
    event_type      TEXT NOT NULL DEFAULT '',
    narrative       TEXT NOT NULL DEFAULT '',
    options         TEXT NOT NULL DEFAULT '[]',
    chosen_option_id TEXT,
    consequences    TEXT NOT NULL DEFAULT '{}',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

_NEW_EVENT_LOGS_COLUMNS = {"realm", "aftermath"}


class TestEventLogsMigration:
    """Verify init_db() applies v1→v2 schema migration for event_logs table."""

    def test_v1_to_v2_adds_realm_and_aftermath_columns(self):
        """Create old-schema DB, run init_db, verify realm & aftermath columns exist in event_logs."""
        db_path = os.path.join(tempfile.gettempdir(), "test_event_logs_migration_cols.db")
        try:
            # Create old-schema database
            conn = get_db(db_path)
            conn.executescript(_OLD_EVENT_LOGS_SCHEMA)
            conn.commit()
            conn.close()

            # Verify old columns are missing before migration
            conn = get_db(db_path)
            old_cols = {
                r[1] for r in conn.execute("PRAGMA table_info(event_logs)")
            }
            for col in _NEW_EVENT_LOGS_COLUMNS:
                assert col not in old_cols, f"{col} should not exist before migration"
            conn.close()

            # Run migration
            conn = get_db(db_path)
            init_db(conn)

            # Verify new columns now exist
            new_cols = {
                r[1] for r in conn.execute("PRAGMA table_info(event_logs)")
            }
            for col in _NEW_EVENT_LOGS_COLUMNS:
                assert col in new_cols, f"{col} should exist after migration"
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_v1_to_v2_old_rows_have_null_realm_and_aftermath(self):
        """Insert row in old schema, run migration, verify realm & aftermath are NULL."""
        db_path = os.path.join(tempfile.gettempdir(), "test_event_logs_migration_rows.db")
        try:
            # Create old-schema database and insert a row
            conn = get_db(db_path)
            conn.executescript(_OLD_EVENT_LOGS_SCHEMA)
            conn.execute("INSERT INTO players (id) VALUES ('p1')")
            conn.execute(
                "INSERT INTO event_logs (player_id, event_index, event_type, narrative) "
                "VALUES ('p1', 0, 'test', 'test narrative')"
            )
            conn.commit()
            conn.close()

            # Run migration
            conn = get_db(db_path)
            init_db(conn)

            # Verify existing row has NULL for new columns
            row = conn.execute(
                "SELECT realm, aftermath FROM event_logs WHERE player_id = 'p1'"
            ).fetchone()
            assert row is not None
            assert row[0] is None, f"Expected realm=NULL, got {row[0]}"
            assert row[1] is None, f"Expected aftermath=NULL, got {row[1]}"
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_v1_to_v2_idempotent(self):
        """Running init_db twice on same DB does not fail, user_version stays 2."""
        db_path = os.path.join(tempfile.gettempdir(), "test_event_logs_migration_idem.db")
        try:
            # Create old-schema database
            conn = get_db(db_path)
            conn.executescript(_OLD_EVENT_LOGS_SCHEMA)
            conn.commit()
            conn.close()

            # First migration
            conn = get_db(db_path)
            init_db(conn)
            conn.close()

            # Second migration - should be a no-op
            conn = get_db(db_path)
            init_db(conn)
            v = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v == 3
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_new_db_has_realm_and_aftermath_columns(self):
        """Brand new database gets realm & aftermath columns in event_logs via schema.sql."""
        db_path = os.path.join(tempfile.gettempdir(), "test_event_logs_migration_new.db")
        try:
            conn = get_db(db_path)
            init_db(conn)

            cols = {
                r[1] for r in conn.execute("PRAGMA table_info(event_logs)")
            }
            for col in _NEW_EVENT_LOGS_COLUMNS:
                assert col in cols, f"{col} should exist in new DB"

            v = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v == 3
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_migration_sets_user_version_to_current(self):
        """Old-schema DB after migration has PRAGMA user_version = 3."""
        db_path = os.path.join(tempfile.gettempdir(), "test_event_logs_migration_ver.db")
        try:
            conn = get_db(db_path)
            conn.executescript(_OLD_EVENT_LOGS_SCHEMA)
            conn.commit()
            conn.close()

            conn = get_db(db_path)
            v_before = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v_before == 0
            conn.close()

            conn = get_db(db_path)
            init_db(conn)

            v_after = conn.execute("PRAGMA user_version").fetchone()[0]
            assert v_after == 3
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
