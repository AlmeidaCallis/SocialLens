import 'dotenv/config';
import pg from 'pg';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const { Pool } = pg;
const here = path.dirname(fileURLToPath(import.meta.url));
export const pool = new Pool({ connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@127.0.0.1:5432/sociallens' });
export async function initDb() {
  const schema = await fs.readFile(path.join(here, 'schema.sql'), 'utf8');
  await pool.query(schema);
}
export async function query(text, params) { return pool.query(text, params); }
export function mapBatch(r) {
  return { _id: String(r.id), title: r.title, platform: r.platform, commentCount: r.comment_count, stats: r.stats, createdAt: r.created_at, updatedAt: r.updated_at };
}
export function mapComment(r) {
  return { _id: String(r.id), batchId: String(r.batch_id), platform: r.platform, originalText: r.original_text, processedText: r.processed_text, sentiment: r.sentiment, sentimentScore: r.sentiment_score, spamStatus: r.spam_status, spamReasons: r.spam_reasons, extractedHashtags: r.extracted_hashtags, extractedMentions: r.extracted_mentions, extractedEntities: r.extracted_entities, preprocessing: r.preprocessing, createdAt: r.created_at };
}
