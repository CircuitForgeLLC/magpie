-- Link posts to opportunities for manual/signal-driven posts.
-- NULL = campaign-scheduled post (existing behaviour).
ALTER TABLE posts ADD COLUMN opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_posts_opportunity ON posts(opportunity_id);
