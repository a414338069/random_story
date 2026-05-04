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

    Parameters
    ----------
    db : sqlite3.Connection or None
        Database connection.  When *None*, a new connection is created via
        ``get_db()``.
    """
    if db is None:
        db = get_db()

    with open(_SCHEMA_PATH, "r") as f:
        schema = f.read()

    db.executescript(schema)
    return db
