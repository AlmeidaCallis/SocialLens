import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import axios from 'axios';
import multer from 'multer';
import pdfParse from 'pdf-parse';
import mammoth from 'mammoth';
import * as XLSX from 'xlsx';
import { pool, initDb, query, mapBatch, mapComment } from './db.js';
dotenv.config();
const app = express();
const PORT = process.env.PORT || 5000;
const NLP = (process.env.NLP_URL || 'http://127.0.0.1:5001').replace(/\/$/, '');
app.use(cors({ origin: process.env.CLIENT_ORIGIN || 'http://localhost:5173' }));
app.use(express.json({ limit: '1mb' }));
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 5 * 1024 * 1024, files: 1 } });
const callNlp = async (route, data) => (await axios.post(`${NLP}/${route}`, data, { timeout: 20000 })).data;
const batchSelect = `SELECT id,title,platform,comment_count,stats,created_at,updated_at FROM analysis_batches`;
const commentSelect = `SELECT id,batch_id,platform,original_text,processed_text,sentiment,sentiment_score,spam_status,spam_reasons,extracted_hashtags,extracted_mentions,extracted_entities,preprocessing,created_at FROM comments`;

app.get('/api/health', async (_req, res) => {
  try { await query('SELECT 1'); res.json({ status: 'ok', service: 'SocialLens API', database: 'connected' }); }
  catch { res.status(503).json({ status: 'error', service: 'SocialLens API', database: 'disconnected' }); }
});

async function analyzeComments({ comments, platform, title }) {
  const batchResult = await query(`INSERT INTO analysis_batches(title,platform,comment_count) VALUES($1,$2,$3) RETURNING id`, [String(title).slice(0,120), platform, comments.length]);
  const batchId = batchResult.rows[0].id;
  const seen = new Set(); const docs = []; const stats = { positive: 0, negative: 0, neutral: 0, spam: 0 };
  try {
    for (const text of comments) {
      const duplicate = seen.has(text.toLowerCase()); seen.add(text.toLowerCase());
      const [sent, spam, extracted, prep] = await Promise.all([
        callNlp('sentiment', { text }), callNlp('spam', { text, duplicate }), callNlp('extract', { text }), callNlp('preprocess', { text })
      ]);
      const doc = { batchId, platform, originalText: text, processedText: prep.cleaned_text, sentiment: sent.sentiment, sentimentScore: sent.confidence, spamStatus: spam.status, spamReasons: spam.reasons || [], extractedHashtags: text.match(/#\w+/g) || [], extractedMentions: text.match(/@\w+/g) || [], extractedEntities: extracted.entities || [], preprocessing: { cleanedText: prep.cleaned_text, stopWordText: prep.stop_word_text, sentimentProbabilities: sent.probabilities || {} } };
      const saved = await query(`INSERT INTO comments(batch_id,platform,original_text,processed_text,sentiment,sentiment_score,spam_status,spam_reasons,extracted_hashtags,extracted_mentions,extracted_entities,preprocessing)
        VALUES($1,$2,$3,$4,$5,$6,$7,$8::jsonb,$9::jsonb,$10::jsonb,$11::jsonb,$12::jsonb) RETURNING id,batch_id,platform,original_text,processed_text,sentiment,sentiment_score,spam_status,spam_reasons,extracted_hashtags,extracted_mentions,extracted_entities,preprocessing,created_at`,
      [batchId, platform, doc.originalText, doc.processedText, doc.sentiment, doc.sentimentScore, doc.spamStatus, JSON.stringify(doc.spamReasons), JSON.stringify(doc.extractedHashtags), JSON.stringify(doc.extractedMentions), JSON.stringify(doc.extractedEntities), JSON.stringify(doc.preprocessing)]);
      docs.push(mapComment(saved.rows[0])); stats[doc.sentiment] = (stats[doc.sentiment] || 0) + 1; if (doc.spamStatus === 'potential_spam') stats.spam++;
    }
    const updated = await query(`UPDATE analysis_batches SET comment_count=$1,stats=$2::jsonb,updated_at=NOW() WHERE id=$3 RETURNING id,title,platform,comment_count,stats,created_at,updated_at`, [docs.length, JSON.stringify(stats), batchId]);
    return { batch: mapBatch(updated.rows[0]), comments: docs };
  } catch (error) {
    await query('DELETE FROM analysis_batches WHERE id=$1', [batchId]);
    throw error;
  }
}
app.post('/api/analysis', async (req,res,next) => {
  try {
    let { comments, platform='other', title='Untitled analysis' } = req.body || {};
    if (!Array.isArray(comments) || !comments.length) return res.status(400).json({error:'comments must be a non-empty array'});
    if (comments.length > 500) return res.status(413).json({error:'Maximum 500 comments per batch'});
    if (!['instagram','facebook','twitter','tiktok','snapchat','other'].includes(platform)) return res.status(400).json({error:'Invalid platform'});
    comments = comments.map(x=>String(x||'').trim()).filter(Boolean);
    if (!comments.length) return res.status(400).json({error:'No non-empty comments found'});
    if (comments.some(x=>x.length>5000)) return res.status(400).json({error:'Each comment must be 5000 characters or fewer'});
    res.status(201).json(await analyzeComments({comments,platform,title}));
  } catch(e) { next(e); }
});
app.post('/api/analysis/preview', upload.single('file'), async (req,res,next) => {
  try {
    if (!req.file) return res.status(400).json({error:'Choose a file to preview'});
    const filename=req.file.originalname.toLowerCase(); let rows=[];
    if(filename.endsWith('.csv')) rows=parseCsv(req.file.buffer.toString('utf8').replace(/^\uFEFF/,''));
    else if(filename.endsWith('.txt')) rows=splitDocumentText(req.file.buffer.toString('utf8'));
    else if(filename.endsWith('.pdf')) { const parsed=await pdfParse(req.file.buffer); rows=splitDocumentText(parsed.text); }
    else if(filename.endsWith('.docx')) { const parsed=await mammoth.extractRawText({buffer:req.file.buffer}); rows=splitDocumentText(parsed.value); }
    else if(filename.endsWith('.xlsx')||filename.endsWith('.xls')) { const wb=XLSX.read(req.file.buffer,{type:'buffer'}); const ws=wb.Sheets[wb.SheetNames[0]]; rows=XLSX.utils.sheet_to_json(ws,{defval:''}).map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,String(v)]))); }
    else return res.status(400).json({error:'Supported formats: CSV, TXT, PDF, DOCX, XLSX and XLS. Legacy .doc is not supported.'});
    if(!rows.length) return res.status(400).json({error:'No readable rows found. Check that the file has text or a header plus data rows.'});
    const keys=Object.keys(rows[0]||{}); const preferred=keys.find(k=>['comment','text','comments','message','content','caption','review'].includes(k.trim().toLowerCase()));
    const column=(req.body.column&&keys.includes(req.body.column))?req.body.column:(preferred||keys[0]);
    const comments=(filename.endsWith('.csv')||filename.endsWith('.xlsx')||filename.endsWith('.xls'))?rows.map(r=>String(r[column]||'').trim()).filter(Boolean):rows.map(r=>String(r.comment||'').trim()).filter(Boolean);
    if(!comments.length) return res.status(400).json({error:`No comments detected. Columns found: ${keys.join(', ')||'none'}. For spreadsheets, use a column named comment, text, content, message, caption or review.`});
    if(comments.length>500) return res.status(413).json({error:`Found ${comments.length} comments; maximum is 500 per batch. Split the file into smaller files.`});
    const tooLong=comments.filter(x=>x.length>5000).length;
    res.json({filename:req.file.originalname,format:filename.split('.').pop(),rowsFound:rows.length,commentCount:comments.length,columns:keys,selectedColumn:column,tooLong,preview:comments.slice(0,8),warnings:[...(tooLong?[`${tooLong} comments exceed 5000 characters and will be rejected during analysis.`]:[]),...(comments.length<rows.length?[`${rows.length-comments.length} blank rows were skipped.`]:[])]});
  } catch(e) { next(e); }
});

app.post('/api/analysis/upload', upload.single('file'), async (req,res,next) => {
  try {
    if (!req.file) return res.status(400).json({error:'Choose a file to upload'});
    const filename=req.file.originalname.toLowerCase();
    let rows=[];
    if(filename.endsWith('.csv')) rows=parseCsv(req.file.buffer.toString('utf8').replace(/^\uFEFF/,''));
    else if(filename.endsWith('.txt')) rows=splitDocumentText(req.file.buffer.toString('utf8'));
    else if(filename.endsWith('.pdf')) { const parsed=await pdfParse(req.file.buffer); rows=splitDocumentText(parsed.text); }
    else if(filename.endsWith('.docx')) { const parsed=await mammoth.extractRawText({buffer:req.file.buffer}); rows=splitDocumentText(parsed.value); }
    else if(filename.endsWith('.xlsx')||filename.endsWith('.xls')) { const wb=XLSX.read(req.file.buffer,{type:'buffer'}); const ws=wb.Sheets[wb.SheetNames[0]]; rows=XLSX.utils.sheet_to_json(ws,{defval:''}).map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,String(v)]))); }
    else return res.status(400).json({error:'Supported file types: CSV, TXT, PDF, DOCX, XLSX and XLS. Legacy .doc files are not supported; save them as .docx first.'});
    if (!rows.length) return res.status(400).json({error:'File contains no readable text or data rows'});
    const keys=Object.keys(rows[0]||{});
    const selected=(req.body.column&&keys.includes(req.body.column))?req.body.column:(keys.find(k=>['comment','text','comments','message','content','caption','review'].includes(k.trim().toLowerCase()))||keys[0]);
    let comments;
    if (filename.endsWith('.csv') || filename.endsWith('.xlsx') || filename.endsWith('.xls')) {
      if (!selected) return res.status(400).json({error:`No comment column found. Available columns: ${keys.join(', ')}. Add a column named comment/text/content or choose the override field.`});
      comments=rows.map(r=>String(r[selected]||'').trim()).filter(Boolean);
    } else comments=rows.map(r=>String(r.comment||'').trim()).filter(Boolean);
    const platform=req.body.platform||'other'; const title=(req.body.title||req.file.originalname).slice(0,120);
    if (!comments.length) return res.status(400).json({error:'No comments found in the file'});
    if (comments.length>500) return res.status(413).json({error:'Maximum 500 comments per batch'});
    if (!['instagram','facebook','twitter','tiktok','snapchat','other'].includes(platform)) return res.status(400).json({error:'Invalid platform'});
    if (comments.some(x=>x.length>5000)) return res.status(400).json({error:'Each comment must be 5000 characters or fewer'});
    res.status(201).json(await analyzeComments({comments,platform,title}));
  } catch(e) { next(e); }
});
function splitDocumentText(value) { const lines=String(value||'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean); const chunks=lines.flatMap(line=>line.length>1500?line.split(/(?<=[.!?])\s+(?=[A-Z0-9])/).map(x=>x.trim()).filter(Boolean):[line]); return chunks.map(comment=>({comment})); }
function parseCsv(s) { const lines=[]; let row=[],cell='',quoted=false; for(let i=0;i<s.length;i++){const c=s[i];if(c==='"'&&quoted&&s[i+1]==='"'){cell+='"';i++;}else if(c==='"'){quoted=!quoted;}else if(c===','&&!quoted){row.push(cell);cell='';}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&s[i+1]==='\n')i++;row.push(cell);if(row.some(v=>v.trim()))lines.push(row);row=[];cell='';}else cell+=c;}row.push(cell);if(row.some(v=>v.trim()))lines.push(row);if(lines.length<2)return [];const headers=lines[0].map(x=>x.trim());return lines.slice(1).map(a=>Object.fromEntries(headers.map((h,i)=>[h,(a[i]||'').trim()])));}
app.get('/api/analysis',async(_req,res,next)=>{try{const r=await query(`${batchSelect} ORDER BY created_at DESC LIMIT 100`);res.json({batches:r.rows.map(mapBatch)});}catch(e){next(e);}});
app.get('/api/analysis/:id',async(req,res,next)=>{try{const b=await query(`${batchSelect} WHERE id=$1`,[req.params.id]);if(!b.rowCount)return res.status(404).json({error:'Batch not found'});const c=await query(`${commentSelect} WHERE batch_id=$1 ORDER BY created_at ASC`,[req.params.id]);res.json({batch:mapBatch(b.rows[0]),comments:c.rows.map(mapComment)});}catch(e){next(e);}});
app.delete('/api/analysis/:id',async(req,res,next)=>{try{const r=await query('DELETE FROM analysis_batches WHERE id=$1 RETURNING id',[req.params.id]);if(!r.rowCount)return res.status(404).json({error:'Batch not found'});res.json({message:'Batch and its comments deleted'});}catch(e){next(e);}});
app.get('/api/comments',async(req,res,next)=>{try{const where=[],params=[];const add=(sql,val)=>{params.push(val);where.push(sql.replace('?',`$${params.length}`));};if(req.query.platform)add('platform = ?',req.query.platform);if(req.query.sentiment)add('sentiment = ?',req.query.sentiment);if(req.query.spamStatus)add('spam_status = ?',req.query.spamStatus);if(req.query.batchId)add('batch_id = ?',req.query.batchId);if(req.query.search)add('original_text ILIKE ?',`%${String(req.query.search).slice(0,100)}%`);params.push(Math.min(Number(req.query.limit)||200,500));const sql=`${commentSelect}${where.length?' WHERE '+where.join(' AND '):''} ORDER BY created_at DESC LIMIT $${params.length}`;const r=await query(sql,params);res.json({comments:r.rows.map(mapComment)});}catch(e){next(e);}});
app.get('/api/comments/:id',async(req,res,next)=>{try{const r=await query(`${commentSelect} WHERE id=$1`,[req.params.id]);if(!r.rowCount)return res.status(404).json({error:'Comment not found'});res.json({comment:mapComment(r.rows[0])});}catch(e){next(e);}});
app.delete('/api/comments/:id',async(req,res,next)=>{try{const r=await query('DELETE FROM comments WHERE id=$1 RETURNING id',[req.params.id]);if(!r.rowCount)return res.status(404).json({error:'Comment not found'});res.json({message:'Comment deleted'});}catch(e){next(e);}});
app.get('/api/dashboard/stats',async(_req,res,next)=>{try{const [total,groups,spam,platforms,recent,words]=await Promise.all([
 query('SELECT COUNT(*)::int AS count FROM comments'),query('SELECT sentiment AS _id,COUNT(*)::int AS count FROM comments GROUP BY sentiment'),query("SELECT COUNT(*)::int AS count FROM comments WHERE spam_status='potential_spam'"),query('SELECT platform AS _id,COUNT(*)::int AS count FROM comments GROUP BY platform'),query(`${batchSelect} ORDER BY created_at DESC LIMIT 5`),query('SELECT processed_text FROM comments ORDER BY created_at DESC LIMIT 2000')]);
 const sentiment={positive:0,negative:0,neutral:0};groups.rows.forEach(g=>{if(g._id)sentiment[g._id]=g.count;});const counts={};for(const c of words.rows){for(const w of (c.processed_text||'').toLowerCase().match(/\b[a-z]{3,}\b/g)||[])counts[w]=(counts[w]||0)+1;}const topWords=Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([word,count])=>({word,count}));res.json({total:total.rows[0].count,sentiment,spam:spam.rows[0].count,platforms:platforms.rows.map(p=>({platform:p._id,count:p.count})),recent:recent.rows.map(mapBatch),topWords});
 }catch(e){next(e);}});
app.get('/api/insights', async (req,res,next) => {
  try {
    const params=[]; const where=[];
    const add=(column,value)=>{params.push(value);where.push(`${column}=$${params.length}`)};
    if(req.query.platform && req.query.platform!=='all') add('platform',req.query.platform);
    if(req.query.sentiment && req.query.sentiment!=='all') add('sentiment',req.query.sentiment);
    if(req.query.spamStatus && req.query.spamStatus!=='all') add('spam_status',req.query.spamStatus);
    if(req.query.from){params.push(req.query.from);where.push(`created_at >= $${params.length}::date`)}
    if(req.query.to){params.push(req.query.to);where.push(`created_at < ($${params.length}::date + INTERVAL '1 day')`)}
    const sql=`SELECT id,batch_id,platform,original_text,processed_text,sentiment,sentiment_score,spam_status,spam_reasons,extracted_hashtags,extracted_mentions,extracted_entities,preprocessing,created_at FROM comments ${where.length?'WHERE '+where.join(' AND '):''} ORDER BY created_at DESC LIMIT 5000`;
    const result=await query(sql,params); const comments=result.rows.map(mapComment);
    const sentiments={positive:0,negative:0,neutral:0,mixed:0}; const platforms={}; const words={}; const topics={}; const hashtags={}; const daily={};
    const stop=new Set('the and for with that this have from your you are was were but not its our they them their about just very really can will what when how all has had she his her him out get got into too also than then there here because been would could should good bad love hate great amazing terrible nice product service delivery price quality issue problem'.split(' '));
    for(const c of comments){sentiments[c.sentiment]=(sentiments[c.sentiment]||0)+1; platforms[c.platform]=(platforms[c.platform]||0)+1; const d=new Date(c.createdAt).toISOString().slice(0,10);daily[d]=(daily[d]||0)+1;
      for(const tag of c.extractedHashtags||[])hashtags[tag]=(hashtags[tag]||0)+1;
      for(const word of (c.processedText||c.originalText||'').toLowerCase().match(/[a-z][a-z0-9_]{2,}/g)||[]){if(!stop.has(word)&&!/^\d+$/.test(word)){words[word]=(words[word]||0)+1;}}
      const toks=(c.processedText||c.originalText||'').toLowerCase().match(/[a-z][a-z0-9_]{2,}/g)||[]; for(let n=0;n<toks.length-1;n++){const phrase=`${toks[n]} ${toks[n+1]}`;if(!stop.has(toks[n])&&!stop.has(toks[n+1]))topics[phrase]=(topics[phrase]||0)+1;}
    }
    const top=obj=>Object.entries(obj).sort((a,b)=>b[1]-a[1]).slice(0,12).map(([label,count])=>({label,count}));
    const positive=sentiments.positive||0,negative=sentiments.negative||0,neutral=sentiments.neutral||0,spam=comments.filter(c=>c.spamStatus==='potential_spam').length;
    const insights=[]; if(comments.length){const p=Math.round(positive/comments.length*100),n=Math.round(negative/comments.length*100),sp=Math.round(spam/comments.length*100);insights.push(`${p}% of filtered comments are labelled positive (${positive} of ${comments.length}).`);if(n>=30)insights.push(`Negative feedback is notable at ${n}%; review recurring topics before drawing conclusions.`);if(sp)insights.push(`${spam} comments (${sp}%) were flagged as potential spam by local rules; review them manually.`);if(top(hashtags).length)insights.push(`Most frequent hashtag: ${top(hashtags)[0].label} (${top(hashtags)[0].count} mentions).`);if(!negative&&!positive)insights.push('Sentiment labels are mostly neutral or unavailable in this filtered set.');}
    res.json({total:comments.length,sentiments,platforms:Object.entries(platforms).map(([platform,count])=>({platform,count})),topWords:top(words),topics:top(topics),hashtags:top(hashtags),daily:Object.entries(daily).sort((a,b)=>a[0].localeCompare(b[0])).map(([date,count])=>({date,count})),spam,insights,comments});
  } catch(e){next(e);}
});

const nlpRoutes={preprocess:'preprocess',ngrams:'ngrams',extract:'extract',linguistic:'linguistic',representations:'representations',sentiment:'sentiment',spam:'spam'};for(const [route,path] of Object.entries(nlpRoutes))app.post(`/api/nlp/${route}`,async(req,res,next)=>{try{res.json(await callNlp(path,req.body||{}));}catch(e){next(e);}});
app.get('/api/nlp/health',async(_req,res)=>{try{res.json((await axios.get(`${NLP}/health`,{timeout:3000})).data);}catch{res.status(503).json({error:'NLP service unavailable'});}});
app.use((err,_req,res,_next)=>{if(err instanceof multer.MulterError)return res.status(413).json({error:'File exceeds 5 MB limit'});if(err.code==='ECONNREFUSED'||err.code==='ECONNABORTED')return res.status(503).json({error:'NLP service unavailable or timed out. Check that Flask is running.'});console.error(err.message);res.status(500).json({error:'Request failed. Check server logs for details.'});});
if(process.env.NODE_ENV!=='test'){
 initDb().then(()=>{console.log('PostgreSQL connected and schema ready');app.listen(PORT,()=>console.log(`SocialLens API listening on http://localhost:${PORT}`));}).catch(e=>{console.error('PostgreSQL initialization failed:',e.message);process.exitCode=1;});
}
export default app;
