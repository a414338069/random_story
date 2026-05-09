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
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id         TEXT DEFAULT NULL,
    save_slot       INTEGER DEFAULT 0,
    age             INTEGER DEFAULT 0,
    cultivation     REAL DEFAULT 0.0,
    ascended        INTEGER DEFAULT 0,
    technique_grades TEXT DEFAULT '[]',
    _pending_breakthrough INTEGER DEFAULT 0,
    _breakthrough_next_req REAL DEFAULT 0.0
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
    realm           TEXT DEFAULT NULL,
    aftermath       TEXT DEFAULT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key       TEXT NOT NULL UNIQUE,
    response        TEXT NOT NULL DEFAULT '{}',
    hit_count       INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_templates (
    id              TEXT PRIMARY KEY,
    type            TEXT NOT NULL DEFAULT '',
    name            TEXT NOT NULL DEFAULT '',
    min_realm       TEXT NOT NULL DEFAULT '',
    max_realm       TEXT NOT NULL DEFAULT '',
    weight          REAL NOT NULL DEFAULT 1.0,
    prompt_template TEXT NOT NULL DEFAULT '',
    fallback_narrative TEXT NOT NULL DEFAULT '',
    default_options TEXT NOT NULL DEFAULT '[]',
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_players_user_slot ON players(user_id, save_slot);

PRAGMA user_version = 3;
