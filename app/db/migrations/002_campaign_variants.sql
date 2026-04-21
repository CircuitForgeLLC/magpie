-- Campaign variants: per-sub (or wildcard) content framing.
-- sub_pattern: exact sub name ("selfhosted"), prefix wildcard ("nd_*"), or "*" for default.
-- Priority: exact match > prefix > "*" default.
CREATE TABLE IF NOT EXISTS campaign_variants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    sub_pattern     TEXT NOT NULL DEFAULT '*',   -- exact sub, glob prefix, or "*" default
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    flair           TEXT,                        -- override flair for this variant
    notes           TEXT,                        -- internal framing notes
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_variants_campaign ON campaign_variants(campaign_id);
