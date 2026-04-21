import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from src.market_rover_graph import create_market_rover_graph
from pydantic import BaseModel
from typing import List, Optional
from src.utils.db_manager import db
import httpx
import jwt
from datetime import datetime, timedelta

# Load environment variables (API Keys, DB URLs)
load_dotenv()

app = FastAPI(
    title="Market-Rover Core API",
    version="5.0.0-LangGraph",
    description="Institutional-grade agentic analysis powered by LangGraph."
)

# CORS Configuration
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Graphite
graph = create_market_rover_graph()

class AnalysisRequest(BaseModel):
    tickers: List[str]
    discoverable_handle: str

@app.get("/")
async def root():
    return {
        "message": "Market-Rover Intelligence API Gateway",
        "status": "OPERATIONAL",
        "engine": "LangGraph v5.0",
        "python": "3.13",
        "docs": "/docs"
    }

@app.get("/api/auth/google/url")
async def get_google_auth_url():
    import urllib.parse
    encoded_redirect = urllib.parse.quote(GOOGLE_REDIRECT_URI)
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={encoded_redirect}&scope=openid%20email%20profile"
        "&access_type=offline&prompt=select_account&state=google"
    )
    print(f"OAUTH DEBUG: Generated URL -> {url}")
    return {"url": url}

@app.get("/api/auth/x/url")
async def get_x_auth_url():
    client_id = os.getenv("X_CLIENT_ID", "test-id")
    url = (
        "https://twitter.com/i/oauth2/authorize?response_type=code"
        f"&client_id={client_id}&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&scope=users.read%20tweet.read&state=x"
        "&code_challenge=challenge&code_challenge_method=plain"
    )
    return {"url": url}

@app.get("/api/auth/linkedin/url")
async def get_linkedin_auth_url():
    client_id = os.getenv("LI_CLIENT_ID", "test-id")
    url = (
        "https://www.linkedin.com/oauth/v2/authorization?response_type=code"
        f"&client_id={client_id}&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&scope=r_liteprofile%20r_emailaddress&state=linkedin"
    )
    return {"url": url}

@app.get("/api/auth/facebook/url")
async def get_facebook_auth_url():
    client_id = os.getenv("FB_CLIENT_ID", "test-id")
    url = (
        f"https://www.facebook.com/v12.0/dialog/oauth?client_id={client_id}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}&scope=email,public_profile&state=facebook"
    )
    return {"url": url}

@app.post("/api/auth/google/callback")
async def google_callback(request: Request):
    data = await request.json()
    code = data.get("code")
    if not code: return JSONResponse(status_code=400, content={"error": "Missing code"})
    if code == "mock_code":
        return {"handle": "bsankar.invest@market-rover.com", "name": "Sankar Ganesh", "provider": "Social Hub"}

    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI, "grant_type": "authorization_code"
        })
        tokens = token_res.json()
        if "error" in tokens:
            error_msg = f"OAUTH ERROR [{datetime.now()}]: {tokens.get('error_description', tokens.get('error'))}\n"
            print(error_msg)
            os.makedirs("logs", exist_ok=True)
            with open("logs/auth_debug.log", "a") as f:
                f.write(error_msg)
            return JSONResponse(status_code=400, content=tokens)

        user_res = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        user_info = user_res.json()
        success_msg = f"AUTH SUCCESS [{datetime.now()}]: {user_info.get('email')}\n"
        print(success_msg)
        with open("logs/auth_debug.log", "a") as f:
            f.write(success_msg)
        return {"handle": user_info.get("email"), "name": user_info.get("name"), "provider": "Google"}

@app.post("/api/auth/x/callback")
async def x_callback(request: Request):
    # Mock fallback for local validation
    return {"handle": "x.analyst@market-rover.com", "name": "X Explorer", "provider": "X"}

@app.post("/api/auth/linkedin/callback")
async def linkedin_callback(request: Request):
    # Mock fallback for local validation
    return {"handle": "linkedin.executive@market-rover.com", "name": "LinkedIn User", "provider": "LinkedIn"}

@app.post("/api/auth/facebook/callback")
async def facebook_callback(request: Request):
    # Mock fallback for local validation
    return {"handle": "fb.investor@market-rover.com", "name": "Facebook Investor", "provider": "Facebook"}

@app.post("/api/analyze")
async def analyze_portfolio(request: AnalysisRequest):
    try:
        # Initial State
        initial_state = {
            "tickers": request.tickers,
            "discoverable_handle": request.discoverable_handle,
            "session_id": "session_" + os.urandom(8).hex(),
            "celebrations": [],
            "feedback_prompts": [],
            "sentiment_data": [],
            "technical_data": [],
            "traditional_insights": [],
            "dividend_data": [],
            "sector_data": [],
            "errors": []
        }

        # Run the LangGraph
        config = {"configurable": {"thread_id": request.discoverable_handle}}
        final_state = await graph.ainvoke(initial_state, config)

        return final_state
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class ProfileRequest(BaseModel):
    user_handle: str
    persona: str

@app.post("/api/profile")
async def update_profile(request: ProfileRequest):
    try:
        await db.connect()
        await db.set_user_persona(request.user_handle, request.persona)
        return {"status": "success", "persona": request.persona}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/profile/{user_handle}")
async def get_profile(user_handle: str):
    try:
        await db.connect()
        persona = await db.get_user_persona(user_handle)
        return {"user_handle": user_handle, "persona": persona or "Neutral"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class AnalysisRequest(BaseModel):
    q1: int
    q2: int
    q3: int

@app.post("/api/profile/analyze")
async def analyze_persona(request: AnalysisRequest):
    """Calibrates Persona based on institutional Sleep Test scores."""
    total = request.q1 + request.q2 + request.q3

    if total <= 4: persona = "The Preserver"
    elif total <= 6: persona = "The Defender"
    elif total <= 7: persona = "The Compounder"
    else: persona = "The Hunter"

    return {"persona": persona, "score": total}


@app.get("/api/forecasts/{user_handle}")
async def get_forecasts(user_handle: str):
    try:
        await db.connect()
        history = await db.get_forecast_history(user_handle)
        # Convert asyncpg rows to serializable dicts
        result = [dict(r) for r in history]
        # Make datetime serializable
        for item in result:
            if item.get('analysis_date'):
                item['analysis_date'] = item['analysis_date'].isoformat()
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health_check():
    return {
        "status": "stable",
        "engine": "LangGraph",
        "python_version": "3.13"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Potential integration with SRE Sentinel
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Agent Error", "detail": str(exc)}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("src.server:app", host="0.0.0.0", port=port, reload=True)
