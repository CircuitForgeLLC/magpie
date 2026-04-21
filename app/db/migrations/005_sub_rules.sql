-- Sub rules: per-subreddit posting rules and capabilities.
-- promo_allowed: NULL = unknown, 1 = allowed, 0 = banned
CREATE TABLE IF NOT EXISTS sub_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform        TEXT NOT NULL DEFAULT 'reddit',
    sub             TEXT NOT NULL,
    flair_required  INTEGER NOT NULL DEFAULT 0,
    flair_to_use    TEXT,
    promo_allowed   INTEGER,                 -- NULL=unknown, 1=yes, 0=hard-banned
    rule_warning    INTEGER NOT NULL DEFAULT 0,  -- shows "Your post may break rules" modal
    notes           TEXT,
    last_checked    TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(platform, sub)
);
