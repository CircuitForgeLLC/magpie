-- Signal monitoring rules: what to watch for across communities
CREATE TABLE IF NOT EXISTS signal_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,                       -- human label ("CF pain points", "Kiwi mentions")
    platform    TEXT    NOT NULL DEFAULT 'reddit',
    sub         TEXT,                                   -- NULL = apply to all monitored subs
    keywords    TEXT    NOT NULL DEFAULT '[]',          -- JSON array of strings
    match_mode  TEXT    NOT NULL DEFAULT 'any',         -- 'any' | 'all' | 'regex'
    min_score   INTEGER NOT NULL DEFAULT 0,             -- ignore posts below this karma score
    label       TEXT,                                   -- signal category: pain-point|feedback|mention|trust
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    notes       TEXT
);

CREATE INDEX IF NOT EXISTS idx_signal_rules_platform_sub ON signal_rules(platform, sub);
CREATE INDEX IF NOT EXISTS idx_signal_rules_active ON signal_rules(active);
