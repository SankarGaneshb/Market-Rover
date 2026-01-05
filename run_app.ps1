# Set environment variable to disable CrewAI telemetry (fixes threading crash)
$env:CREWAI_TELEMETRY_OPT_OUT = 'true'

# Run Streamlit Application
streamlit run app.py
