-- Add optional post_url to sub_rules.
-- When set, the Copy & Post modal links here instead of /r/{sub}/submit.
-- Use for megathreads, weekly threads, or any pinned destination.
ALTER TABLE sub_rules ADD COLUMN post_url TEXT;
