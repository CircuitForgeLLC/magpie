-- Migration 019: Add link_url to campaign_variants
-- Supports link-style posts (Reddit link posts, Lemmy link posts) where the URL
-- appears as the post link rather than embedded in the body. Also useful for
-- one-click copying the canonical URL from the variant editor UI.
ALTER TABLE campaign_variants ADD COLUMN link_url TEXT;
