CREATE TABLE IF NOT EXISTS analysis_batches (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(120) NOT NULL DEFAULT 'Untitled analysis',
  platform VARCHAR(20) NOT NULL DEFAULT 'other' CHECK (platform IN ('instagram','facebook','twitter','tiktok','snapchat','other')),
  comment_count INTEGER NOT NULL DEFAULT 0,
  stats JSONB NOT NULL DEFAULT '{"positive":0,"negative":0,"neutral":0,"spam":0}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS comments (
  id BIGSERIAL PRIMARY KEY,
  batch_id BIGINT NOT NULL REFERENCES analysis_batches(id) ON DELETE CASCADE,
  platform VARCHAR(20) NOT NULL DEFAULT 'other' CHECK (platform IN ('instagram','facebook','twitter','tiktok','snapchat','other')),
  original_text TEXT NOT NULL,
  processed_text TEXT,
  sentiment VARCHAR(20) CHECK (sentiment IN ('positive','negative','neutral')),
  sentiment_score DOUBLE PRECISION,
  spam_status VARCHAR(30) CHECK (spam_status IN ('normal','potential_spam')),
  spam_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
  extracted_hashtags JSONB NOT NULL DEFAULT '[]'::jsonb,
  extracted_mentions JSONB NOT NULL DEFAULT '[]'::jsonb,
  extracted_entities JSONB NOT NULL DEFAULT '[]'::jsonb,
  preprocessing JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS comments_batch_id_idx ON comments(batch_id);
CREATE INDEX IF NOT EXISTS comments_platform_idx ON comments(platform);
CREATE INDEX IF NOT EXISTS comments_sentiment_idx ON comments(sentiment);
CREATE INDEX IF NOT EXISTS comments_spam_status_idx ON comments(spam_status);
CREATE INDEX IF NOT EXISTS comments_created_at_idx ON comments(created_at DESC);
CREATE INDEX IF NOT EXISTS comments_original_text_search_idx ON comments USING GIN (to_tsvector('simple', original_text));

-- Upgrade existing databases created by earlier SocialLens versions.
ALTER TABLE analysis_batches DROP CONSTRAINT IF EXISTS analysis_batches_platform_check;
ALTER TABLE analysis_batches ADD CONSTRAINT analysis_batches_platform_check CHECK (platform IN ('instagram','facebook','twitter','tiktok','snapchat','other'));
ALTER TABLE comments DROP CONSTRAINT IF EXISTS comments_platform_check;
ALTER TABLE comments ADD CONSTRAINT comments_platform_check CHECK (platform IN ('instagram','facebook','twitter','tiktok','snapchat','other'));
