# Market-Rover Unified Monolith Launcher
# Usage: .\run_dev.ps1

$ROOT = $PSScriptRoot

Write-Host "🚀 Launching Unified Market-Rover Monolith Ecosystem..." -ForegroundColor Cyan

# 1. Unified Backend Gateway (Port 8080)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT'; `$env:PYTHONPATH='$ROOT;$ROOT\market_rover\backend;$ROOT\pledge_rover\backend;$ROOT\hil_rover\backend;$ROOT\ownerise\backend'; Write-Host '--- Market-Rover Unified Gateway (Port 8080) ---' -ForegroundColor Yellow; python -m uvicorn server:app --reload --host 127.0.0.1 --port 8080"

Write-Host "✅ Unified server started on http://127.0.0.1:8080!" -ForegroundColor Green
Write-Host "   • Health Check : http://127.0.0.1:8080/health" -ForegroundColor Green
Write-Host "   • OpenAPI Docs : http://127.0.0.1:8080/docs" -ForegroundColor Green
