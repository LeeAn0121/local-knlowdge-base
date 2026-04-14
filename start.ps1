# Start API server and Next.js web UI together
$ErrorActionPreference = "Stop"

Write-Host "Starting RAG Knowledge Base..." -ForegroundColor Cyan

# Start FastAPI
$api = Start-Process python -ArgumentList "-m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000" `
    -WorkingDirectory $PSScriptRoot -PassThru -NoNewWindow

# Start Next.js
$web = Start-Process npm -ArgumentList "run dev" `
    -WorkingDirectory "$PSScriptRoot\web" -PassThru -NoNewWindow

Write-Host "API  -> http://localhost:8000" -ForegroundColor Green
Write-Host "UI   -> http://localhost:3000" -ForegroundColor Green
Write-Host "Docs -> http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop both services..." -ForegroundColor Yellow

try {
    Wait-Process $api.Id
} finally {
    Stop-Process $api -ErrorAction SilentlyContinue
    Stop-Process $web -ErrorAction SilentlyContinue
    Write-Host "Services stopped." -ForegroundColor Red
}
