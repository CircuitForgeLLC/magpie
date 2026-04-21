-- Campaign subs: which subreddits a campaign posts to, and in what order.
CREATE TABLE IF NOT EXISTS campaign_subs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    sub             TEXT NOT NULL,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    active          INTEGER NOT NULL DEFAULT 1,

    UNIQUE(campaign_id, sub)
);

CREATE INDEX IF NOT EXISTS idx_campaign_subs_campaign ON campaign_subs(campaign_id);
