# Market Rover - Easy Run Script
# This script properly loads the OPENAI_API_KEY from .env and runs Market Rover

# Activate virtual environment
if (-not $env:VIRTUAL_ENV) {
    .\venv\Scripts\Activate.ps1
}

# Load OPENAI_API_KEY from .env file
$envFile = Get-Content .env
foreach ($line in $envFile) {
    if ($line -match "^OPENAI_API_KEY=(.+)$") {
        $env:OPENAI_API_KEY = $matches[1].Trim()
        Write-Host "✅ Loaded OPENAI_API_KEY from .env" -ForegroundColor Green
        break
    }
}

# Verify key is loaded
if (-not $env:OPENAI_API_KEY) {
    Write-Host "❌ ERROR: OPENAI_API_KEY not found in .env file!" -ForegroundColor Red
    Write-Host "Please add your OpenAI API key to the .env file" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Starting Market Rover..." -ForegroundColor Cyan
Write-Host ""

# Run Market Rover
python main.py
