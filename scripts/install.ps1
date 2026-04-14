# Installation script for Windows
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent

Write-Host "=== RAG Knowledge Base - Installation ===" -ForegroundColor Cyan
Write-Host ""

# Check Ollama
Write-Host "Checking Ollama..." -ForegroundColor Yellow
try {
    $null = Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 3
    Write-Host "  Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "  Ollama not running. Install from https://ollama.com and run it first." -ForegroundColor Red
    exit 1
}

# Pull models
Write-Host "Pulling Ollama models..." -ForegroundColor Yellow
& ollama pull nomic-embed-text
& ollama pull llama3.2:3b
Write-Host "  Models ready" -ForegroundColor Green

# Python venv
Write-Host "Setting up Python environment..." -ForegroundColor Yellow
Set-Location $Root
python -m venv .venv
& .\.venv\Scripts\pip install -e . --quiet
Write-Host "  Python packages installed" -ForegroundColor Green

# Node
Write-Host "Setting up Node.js environment..." -ForegroundColor Yellow
Set-Location "$Root\web"
npm install --silent
Write-Host "  Node packages installed" -ForegroundColor Green

# .env
Set-Location $Root
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
    Write-Host "Edit DOCS_PATH in .env to point to your markdown files." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Installation complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env: set DOCS_PATH to your markdown directory"
Write-Host "  2. Activate venv: .\.venv\Scripts\activate"
Write-Host "  3. Index documents: rag index --verbose"
Write-Host "  4. Start services: rag serve"
Write-Host "     OR: .\start.ps1"
