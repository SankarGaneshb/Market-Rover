# Market-Rover 2.0 Web UI Launcher (PowerShell)
Write-Host "Starting Market-Rover 2.0 Web UI..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Launch Streamlit app
streamlit run app.py --server.port 8501 --server.address localhost
