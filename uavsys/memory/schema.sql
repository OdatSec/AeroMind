CREATE TABLE IF NOT EXISTS episodic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    agent TEXT NOT NULL,
    layer TEXT DEFAULT 'episodic',
    content_json TEXT, -- Full event details
    text TEXT,         -- Searchable text representation
    source TEXT,
    trust REAL,
    importance REAL DEFAULT 0.5,
    attack_tag TEXT,
    embed_id INTEGER
);

CREATE TABLE IF NOT EXISTS semantic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    agent TEXT,
    layer TEXT DEFAULT 'semantic',
    key TEXT,
    value TEXT,
    confidence REAL,
    source_episode_id INTEGER,
    category TEXT,  -- ontology: target | environment | operational
    source TEXT,
    trust REAL,
    importance REAL DEFAULT 0.7,
    attack_tag TEXT,
    embed_id INTEGER
);

CREATE TABLE IF NOT EXISTS procedural (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    agent TEXT,
    layer TEXT DEFAULT 'procedural',
    name TEXT,
    description TEXT,
    steps_json TEXT,
    source TEXT,
    trust REAL,
    importance REAL DEFAULT 0.8,
    attack_tag TEXT,
    embed_id INTEGER
);

CREATE TABLE IF NOT EXISTS coordination (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    agent TEXT,
    layer TEXT DEFAULT 'coordination',
    from_agent TEXT,
    to_agent TEXT,
    intent TEXT,
    message TEXT,
    status TEXT,
    source TEXT,
    trust REAL,
    importance REAL DEFAULT 0.6,
    attack_tag TEXT,
    embed_id INTEGER
);

CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    model TEXT,
    text TEXT,
    vector_json TEXT -- Stored as JSON array of floats
);

CREATE TABLE IF NOT EXISTS tool_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL UNIQUE,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    last_used TEXT,
    avg_context TEXT  -- Optional: common args/conditions as JSON
);
