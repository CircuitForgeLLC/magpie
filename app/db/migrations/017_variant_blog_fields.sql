-- 017_variant_blog_fields.sql

-- slug: Directus URL slug. Generated from title via slugify() if NULL.
ALTER TABLE campaign_variants ADD COLUMN slug TEXT;

-- tags: JSON array of tag strings. e.g. '["self-hosting","peregrine"]'
-- NULL = no tags.
ALTER TABLE campaign_variants ADD COLUMN tags TEXT;

-- seo_description: Short meta description for search engines (max ~160 chars).
-- NULL = Directus default.
ALTER TABLE campaign_variants ADD COLUMN seo_description TEXT;
