-- Make campaign_id nullable on posts to support manual opportunity posts
-- that don't belong to a campaign. SQLite requires a full table rebuild
-- to drop a NOT NULL constraint.
CREATE TABLE posts_new (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    variant_id      INTEGER REFERENCES campaign_variants(id),
    opportunity_id  INTEGER REFERENCES opportunities(id) ON DELETE SET NULL,
    platform        TEXT NOT NULL DEFAULT 'reddit',
    target          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    url             TEXT,
    error_msg       TEXT,
    screenshot_path TEXT,
    triggered_by    TEXT DEFAULT 'scheduler',
    posted_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO posts_new SELECT id, campaign_id, variant_id, opportunity_id, platform, target, status, url, error_msg, screenshot_path, triggered_by, posted_at FROM posts;

DROP TABLE posts;
ALTER TABLE posts_new RENAME TO posts;

CREATE INDEX IF NOT EXISTS idx_posts_campaign ON posts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_posts_opportunity ON posts(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_posts_target ON posts(target);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
