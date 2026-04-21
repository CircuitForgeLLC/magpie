-- Engagement snapshots: periodic metric pulls after posting.
CREATE TABLE IF NOT EXISTS engagement (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    score       INTEGER,
    upvotes     INTEGER,
    comments    INTEGER,
    awards      INTEGER DEFAULT 0,
    checked_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_engagement_post ON engagement(post_id);
CREATE INDEX IF NOT EXISTS idx_engagement_checked_at ON engagement(checked_at);
