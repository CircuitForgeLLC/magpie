-- app/db/migrations/016_campaign_subs_comment_config.sql

-- thread_title_pattern: case-insensitive substring to match the sticky thread title.
-- Required for reddit_comment campaigns; NULL for reddit_post campaigns.
ALTER TABLE campaign_subs ADD COLUMN thread_title_pattern TEXT;

-- thread_url_override: skip thread detection and comment directly on this URL.
-- Takes precedence over thread_title_pattern when set.
ALTER TABLE campaign_subs ADD COLUMN thread_url_override TEXT;

-- occurrence: scheduling modifier applied inside the job runner before execution.
-- "every"        — fire on every scheduled run (default)
-- "first_sunday" — fire only on the first Sunday of the month
-- NULL           — treated as "every"
ALTER TABLE campaign_subs ADD COLUMN occurrence TEXT;
