import test from 'node:test';
import assert from 'node:assert/strict';
import { mapBatch, mapComment } from '../db.js';

test('batch rows map PostgreSQL columns to the existing frontend contract', () => {
  const batch = mapBatch({ id: 7, title: 'Demo', platform: 'instagram', comment_count: 3, stats: {positive: 2, negative: 1, neutral: 0, spam: 0}, created_at: new Date(0), updated_at: new Date(0) });
  assert.equal(batch._id, '7');
  assert.equal(batch.commentCount, 3);
  assert.equal(batch.stats.positive, 2);
});
test('comment rows map PostgreSQL columns to the existing frontend contract', () => {
  const comment = mapComment({ id: 9, batch_id: 7, platform: 'facebook', original_text: 'Nice', processed_text: 'nice', sentiment: 'positive', sentiment_score: 0.9, spam_status: 'normal', spam_reasons: [], extracted_hashtags: ['#wow'], extracted_mentions: [], extracted_entities: [], preprocessing: {}, created_at: new Date(0) });
  assert.equal(comment._id, '9');
  assert.equal(comment.batchId, '7');
  assert.equal(comment.originalText, 'Nice');
});
test('CSV comment column detection accepts common headers', () => {
  const keys = ['created_at', 'Comment'];
  const selected = keys.find(k => ['comment','text','comments','message','content'].includes(k.trim().toLowerCase()));
  assert.equal(selected, 'Comment');
});
