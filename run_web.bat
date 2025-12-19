@echo off
REM Market-Rover 2.0 Web UI Launcher
echo Starting Market-Rover 2.0 Web UI...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Launch Streamlit app
streamlit run app.py --server.port 8501 --server.address localhost

pause
