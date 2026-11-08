Set-Location "$PSScriptRoot\backend"
if (-not (Test-Path ".env")) { Copy-Item .env.example .env; Write-Host "Update backend\.env with your PostgreSQL password before running if needed." -ForegroundColor Yellow }
if (-not (Test-Path "node_modules")) { npm install }
npm run dev
