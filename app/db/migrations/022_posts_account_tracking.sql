-- Migration 022: Track which account made each post
-- NULL = posted by the default account (alan_reddit) before multi-user was added.
ALTER TABLE posts ADD COLUMN posted_by_account_id INTEGER REFERENCES team_accounts(id);
