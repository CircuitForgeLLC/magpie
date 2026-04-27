-- app/db/migrations/015_campaign_type.sql
ALTER TABLE campaigns ADD COLUMN type TEXT NOT NULL DEFAULT 'reddit_post';
