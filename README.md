# SocialLens — Retro Glass Comment Intelligence

SocialLens is a local full-stack learning project for analyzing supplied social-media comments. It does **not** scrape or log in to Instagram, Facebook, X/Twitter, TikTok or Snapchat. Choose a platform label and paste comments or upload a supported file.

## Project Demo Video

Watch the working demonstration of SocialLens:
https://drive.google.com/file/d/1pxHwabrR5_kDkI7OLoB2KQG1GMpJeM03/view?usp=sharing

## Folder layout

- `frontend/` — React + Vite interface, retro teal glassmorphism theme, dashboard, analysis, comment manager, NLP lab and reports.
- `backend/` — Express API, PostgreSQL schema, comment persistence, file parsing and CSV/Excel exports from the UI.
- `python/` — Flask NLP service: sentiment estimates, spam screening, preprocessing, regex extraction, linguistic analysis, n-grams and text representations.
- `sample_data/` — sample CSV comments.

## Requirements

- Node.js 20+ (Node 22 is fine)
- Python 3.10 recommended for this project
- PostgreSQL installed and running, with a database named `sociallens`

## First-time setup

### 1. Database

Create a PostgreSQL database named `sociallens`. In `backend/`, copy `.env.example` to `.env` and replace `YOUR_POSTGRES_PASSWORD` with your local PostgreSQL password. Do not share or commit `.env`.

### 2. Install frontend dependencies

```powershell
cd frontend
npm install
```

### 3. Install backend dependencies

```powershell
cd ..\backend
npm install
```

### 4. Install Python dependencies

```powershell
cd ..\python
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m nltk.downloader punkt punkt_tab stopwords wordnet omw-1.4
```

If your local project already has a working `.venv`, keep using it rather than recreating it.

## Run the app (three terminals)

Run these in three separate PowerShell terminals and leave them open:

**Terminal 1 — Python NLP**
```powershell
cd D:\path\to\SocialLens\python
.\.venv\Scripts\Activate.ps1
python app.py
```

**Terminal 2 — backend**
```powershell
cd D:\path\to\SocialLens\backend
npm run dev
```

**Terminal 3 — frontend**
```powershell
cd D:\path\to\SocialLens\frontend
npm run dev
```

Open `http://localhost:5173`. The backend health endpoint is `http://localhost:5000/api/health`; the NLP health endpoint is `http://127.0.0.1:5001/health`.

Root-level convenience scripts `start-python.ps1`, `start-backend.ps1`, and `start-frontend.ps1` are also included; run each in its own terminal.

## Supported input and exports

- Paste comments (one per line) or upload `CSV`, `TXT`, `PDF`, `DOCX`, `XLSX` or `XLS` (maximum 5 MB; 500 comments per batch).
- For CSV/Excel, SocialLens looks for a column called `comment`, `text`, `comments`, `message`, `content`, `caption` or `review`; if none is found, it uses the first column.
- Legacy `.doc` is not parsed directly; save it as `.docx` first.
- Export results as CSV or Excel (`.xlsx`) and select a platform or all platforms in the Comment Manager.
- Platform names are labels only. Official platform API integration is not included.

## NLP behavior and limitations

- Sentiment combines a small TF-IDF/logistic-regression teaching model with a transparent sentiment lexicon and returns estimated class probabilities. The probability is not a guarantee; the corpus is small and synthetic, so do not claim production accuracy.
- Spam screening uses explainable heuristic patterns and duplicate checks. A flag is a review signal, not proof of malicious intent. A new domain or scam phrasing may evade rules; legitimate promotions may also be flagged.
- PDF/DOCX extraction depends on document text being selectable. Scanned PDFs need OCR, which is not included.
- For a reliable sentiment model, collect a legally usable, representative labelled dataset, split train/validation/test data, evaluate per-class precision/recall/F1, then retrain and compare before deployment.

## Database

PostgreSQL tables are created/updated by `backend/schema.sql` when the backend starts. Existing installations get platform constraint updates for Instagram, Facebook, X/Twitter, TikTok, Snapchat and Other. Make a backup before applying schema changes to important data.

## Phase 4–6 additions (file validation, trends, reports)

- **Import preview & validation:** On Analyze Comments, select a file and choose **Preview & validate file** before analysis. The preview shows the detected comment count, source columns, selected column, sample rows and warnings. Upload is capped at 5 MB and 500 comments. Supported inputs: CSV, TXT, PDF, DOCX, XLSX and XLS. Text extraction from scanned PDFs is not supported in this phase.
- **Trends & Insights:** New sidebar page at `/insights`. Filter saved comments by platform, sentiment, spam status and date range. See platform counts, saved-comment volume over time, recurring adjacent-word phrases, extracted hashtags and automatically generated descriptive insights. The app does not connect to or scrape live social-media feeds.
- **Exports:** Export filtered comment records to CSV or Excel (`.xlsx`). PDF is provided through the browser's **Print / Save as PDF** dialog. Allow pop-ups for PDF report generation. Browser print layout is a simple, readable report rather than a server-generated PDF file.
- **Data safety:** No database reset or destructive migration was added. The new endpoints read existing comments and batches; they do not alter existing PostgreSQL records.

### New API endpoints

- `POST /api/analysis/preview` — multipart form field `file`; validates/extracts a file and returns detected count, columns, first eight comments and warnings without saving or analyzing the comments.
- `GET /api/insights` — optional query parameters: `platform`, `sentiment`, `spamStatus`, `from` (`YYYY-MM-DD`), `to` (`YYYY-MM-DD`). Returns up to 5,000 matching saved comments plus aggregates and evidence summaries.

### Validation note

The updated backend passed `node --check`. The React JSX passed TypeScript's JSX transpilation/parser check. A full Vite production build could not be run in this environment because dependencies were not installed before the install command timed out. Run `npm install` and `npm run build` in `frontend` on your machine before replacing your current working folder.
