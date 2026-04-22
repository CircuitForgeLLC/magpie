-- Surfaced content instances from signal monitoring
CREATE TABLE IF NOT EXISTS signals (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    platform         TEXT    NOT NULL DEFAULT 'reddit',
    sub              TEXT    NOT NULL,
    post_id          TEXT    NOT NULL,              -- platform-native ID (reddit: t3_xxxxx)
    title            TEXT    NOT NULL,
    body_snippet     TEXT,                          -- first ~500 chars
    score            INTEGER,
    comment_count    INTEGER,
    author           TEXT,
    url              TEXT,
    posted_at        TEXT,                          -- original post timestamp
    surfaced_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    matched_keywords TEXT    NOT NULL DEFAULT '[]', -- JSON array of matched terms
    status           TEXT    NOT NULL DEFAULT 'new',-- new|saved|dismissed
    notes            TEXT,
    UNIQUE(platform, post_id)                       -- deduplicate across rule runs
);

-- Junction table: which rules matched each signal (many-to-many)
CREATE TABLE IF NOT EXISTS signal_rule_matches (
    signal_id   INTEGER NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
    rule_id     INTEGER NOT NULL REFERENCES signal_rules(id) ON DELETE CASCADE,
    matched_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (signal_id, rule_id)
);

CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_platform_sub ON signals(platform, sub);
CREATE INDEX IF NOT EXISTS idx_signals_surfaced_at ON signals(surfaced_at DESC);
CREATE INDEX IF NOT EXISTS idx_signal_rule_matches_rule ON signal_rule_matches(rule_id);
