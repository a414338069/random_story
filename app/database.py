import os
import sqlite3

_SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "schema.sql"
)
_DEFAULT_DB_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data"
)
DEFAULT_DB_PATH = os.path.join(_DEFAULT_DB_DIR, "rebirth.db")


def get_db(db_path=None):
    """Create a new sqlite3 connection with recommended pragmas.

    Parameters
    ----------
    db_path : str or None
        Path to the SQLite database file.  Use ``":memory:"`` for in-memory
        databases.  When *None*, the default path ``app/data/rebirth.db`` is
        used and its parent directory is created if needed.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
        os.makedirs(_DEFAULT_DB_DIR, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db=None):
    """Read and execute schema.sql on the given connection.

    Uses ``PRAGMA user_version`` to detect and apply migrations for
    existing databases without destructively re-creating tables.

    Parameters
    ----------
    db : sqlite3.Connection or None
        Database connection.  When *None*, a new connection is created via
        ``get_db()``.
    """
    if db is None:
        db = get_db()

    # Read current version BEFORE schema.sql may set it to 1
    version = db.execute("PRAGMA user_version").fetchone()[0]

    # Check if players table already exists (old DB needing migration)
    table_exists = (
        db.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='players'"
        ).fetchone()
        is not None
    )

    # Migration v0 → v1: add save-system columns to existing table first,
    # so the CREATE INDEX in schema.sql won't fail on missing columns.
    if version < 1 and table_exists:
        table_info = db.execute("PRAGMA table_info(players)").fetchall()
        columns = {row[1] for row in table_info}

        if "age" not in columns:
            _MIGRATIONS = [
                "ALTER TABLE players ADD COLUMN user_id TEXT DEFAULT NULL",
                "ALTER TABLE players ADD COLUMN save_slot INTEGER DEFAULT 0",
                "ALTER TABLE players ADD COLUMN age INTEGER DEFAULT 0",
                "ALTER TABLE players ADD COLUMN cultivation REAL DEFAULT 0.0",
                "ALTER TABLE players ADD COLUMN ascended INTEGER DEFAULT 0",
                "ALTER TABLE players ADD COLUMN technique_grades TEXT DEFAULT '[]'",
                "ALTER TABLE players ADD COLUMN _pending_breakthrough INTEGER DEFAULT 0",
                "ALTER TABLE players ADD COLUMN _breakthrough_next_req REAL DEFAULT 0.0",
            ]
            for stmt in _MIGRATIONS:
                db.execute(stmt)

    # Schema.sql handles CREATE TABLE IF NOT EXISTS (new DBs) and CREATE INDEX
    with open(_SCHEMA_PATH, "r") as f:
        schema = f.read()
    db.executescript(schema)

    if version < 1:
        db.execute("PRAGMA user_version = 1")

    # Migration v1 → v2: add realm and aftermath columns to event_logs
    if version < 2:
        event_logs_exists = (
            db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='event_logs'"
            ).fetchone()
            is not None
        )
        if event_logs_exists:
            table_info = db.execute("PRAGMA table_info(event_logs)").fetchall()
            columns = {row[1] for row in table_info}
            if "realm" not in columns:
                db.execute(
                    "ALTER TABLE event_logs ADD COLUMN realm TEXT DEFAULT NULL"
                )
            if "aftermath" not in columns:
                db.execute(
                    "ALTER TABLE event_logs ADD COLUMN aftermath TEXT DEFAULT NULL"
                )
        db.execute("PRAGMA user_version = 2")

    return db
