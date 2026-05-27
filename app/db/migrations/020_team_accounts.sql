-- Migration 020: Team accounts table
-- Tracks all posting identities across platforms (personal and official).
-- session_file is an absolute path to the session JSON; NULL for accounts
-- that post manually (Neon) or whose sessions haven't been established yet.
CREATE TABLE IF NOT EXISTS team_accounts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    platform     TEXT NOT NULL,                        -- reddit | lemmy | mastodon | bluesky
    username     TEXT NOT NULL,                        -- u/pyr0ball, @cf@floss.social, etc.
    account_type TEXT NOT NULL DEFAULT 'personal',     -- personal | official
    session_file TEXT,                                 -- absolute path; NULL = manual posting only
    active       INTEGER NOT NULL DEFAULT 1,
    notes        TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(platform, username)
);
