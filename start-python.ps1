Set-Location "$PSScriptRoot\python"
if (-not (Test-Path ".venv")) { py -3.10 -m venv .venv }
& .\.venv\Scripts\Activate.ps1
if (-not (Test-Path ".venv\sociallens-deps-installed")) { pip install -r requirements.txt; python -m nltk.downloader punkt punkt_tab stopwords wordnet omw-1.4; New-Item .venv\sociallens-deps-installed -ItemType File | Out-Null }
python app.py
