-- Posts: individual post attempts, one row per sub per campaign run.
-- status: pending | running | success | failed | skipped (dupe guard)
CREATE TABLE IF NOT EXISTS posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL REFERENCES campaigns(id),
    variant_id      INTEGER REFERENCES campaign_variants(id),
    platform        TEXT NOT NULL DEFAULT 'reddit',
    target          TEXT NOT NULL,           -- subreddit name
    status          TEXT NOT NULL DEFAULT 'pending',
    url             TEXT,                    -- permalink if succeeded
    error_msg       TEXT,
    screenshot_path TEXT,
    triggered_by    TEXT DEFAULT 'scheduler', -- scheduler | manual
    posted_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_posts_campaign ON posts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_posts_target ON posts(target);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
