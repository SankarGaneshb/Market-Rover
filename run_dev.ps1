# Market-Rover v5 Dev Launcher (Improved)
# Usage: .\run_dev.ps1

$ROOT = $PSScriptRoot

Write-Host "🚀 Launching Market-Rover v5 Ecosystem..." -ForegroundColor Cyan

# 1. Market-Rover Backend (8080)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT\market_rover\backend'; `$env:PYTHONPATH='$ROOT;.'; Write-Host '--- Market-Rover Backend (8080) ---' -ForegroundColor Yellow; uvicorn src.server:app --reload --port 8080"

# 2. Market-Rover Frontend (5173)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT\market_rover\frontend'; Write-Host '--- Market-Rover UI (5173) ---' -ForegroundColor Cyan; npm run dev"

# 3. HIL-Rover Backend (8081)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT\hil_rover\backend'; `$env:PYTHONPATH='$ROOT;.'; Write-Host '--- HIL-Rover Backend (8081) ---' -ForegroundColor Magenta; uvicorn src.server:app --reload --port 8081"

# 4. HIL-Rover Frontend (5174)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT\hil_rover\frontend'; Write-Host '--- HIL-Rover UI (5174) ---' -ForegroundColor Green; npm run dev"

Write-Host "✅ All services requested. Follow the individual windows for logs!" -ForegroundColor Green
