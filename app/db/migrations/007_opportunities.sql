-- Opportunities: flagged threads/posts queued for human review before posting.
-- Covers both auto-post (Reddit via Playwright) and manual handoff (Lemmy, LinkedIn, etc.)
CREATE TABLE IF NOT EXISTS opportunities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT NOT NULL DEFAULT 'reddit',
    community     TEXT NOT NULL,           -- sub name, lemmy community, etc.
    thread_url    TEXT NOT NULL,
    thread_title  TEXT,
    thread_body   TEXT,                    -- snippet of original post for context
    signal_reason TEXT,                    -- why this was flagged
    product       TEXT,                    -- peregrine, kiwi, snipe, circuitforge
    draft_title   TEXT,                    -- for new_post type; NULL for replies
    draft_body    TEXT NOT NULL DEFAULT '',
    post_type     TEXT NOT NULL DEFAULT 'reply_to_thread',  -- reply_to_thread | new_post
    status        TEXT NOT NULL DEFAULT 'pending_review',   -- pending_review | approved | posted | manual_posted | dismissed
    campaign_id   INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
    dismiss_note  TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_opportunities_status   ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_platform ON opportunities(platform, community);
