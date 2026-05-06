-- Add per-sub post cap; NULL = unlimited (evergreen). Set max_posts=1 for one-shot intro campaigns.
ALTER TABLE campaign_subs ADD COLUMN max_posts INTEGER;
