-- Campaigns: a named posting campaign for a product on a platform.
-- cron_schedule uses standard cron syntax (e.g. "0 9 * * 2" = Tuesday 9 AM)
CREATE TABLE IF NOT EXISTS campaigns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    product         TEXT NOT NULL,           -- peregrine, kiwi, snipe, circuitforge
    platform        TEXT NOT NULL DEFAULT 'reddit',
    cron_schedule   TEXT,                    -- NULL = manual trigger only
    active          INTEGER NOT NULL DEFAULT 1,
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_campaigns_product ON campaigns(product);
CREATE INDEX IF NOT EXISTS idx_campaigns_active ON campaigns(active);
