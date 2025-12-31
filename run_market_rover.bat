@echo off
REM Run Market Rover in Production Mode
echo 🚀 Launching Market Rover 2.0...
echo 🔧 Environment: Production
echo 🧹 Cleaning cache...
if exist __pycache__ rd /s /q __pycache__
.\.venv\Scripts\python.exe -m streamlit run app.py
pause
