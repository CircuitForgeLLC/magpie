-- Per-sub cursor state for the signal scraper.
-- Stores the newest post fullname seen so subsequent runs only fetch newer posts.
CREATE TABLE IF NOT EXISTS signal_scrape_state (
    platform        TEXT NOT NULL DEFAULT 'reddit',
    sub             TEXT NOT NULL,
    last_fullname   TEXT,               -- e.g. t3_abc123; NULL = never scraped
    last_scraped_at TEXT,
    posts_seen      INTEGER NOT NULL DEFAULT 0,
    signals_found   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (platform, sub)
);
