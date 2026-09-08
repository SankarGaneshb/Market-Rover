"""
Auth routes — Google OAuth 2.0 flow.
Extracted from server.py (was inline endpoints).
"""
import os
import urllib.parse
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

def get_redirect_uri(request: Request) -> str:
    env_uri = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    if env_uri:
        return env_uri

    host = request.headers.get("host", "")
    proto = request.headers.get("x-forwarded-proto", "https" if "run.app" in host else "http")
    if host and "localhost" not in host and "127.0.0.1" not in host:
        return f"{proto}://{host}"

    return "https://market-rover-app-9514347926.us-central1.run.app"


@router.get("/google/url")
async def get_google_auth_url(request: Request):
    redirect_uri = get_redirect_uri(request)

    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": "google"
    }

    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    return {"url": url}

@router.get("/x/url")
async def get_x_auth_url(request: Request):
    client_id = os.getenv("X_CLIENT_ID", "test-id")
    redirect_uri = get_redirect_uri(request)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "users.read tweet.read",
        "state": "x",
        "code_challenge": "challenge",
        "code_challenge_method": "plain"
    }
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return {"url": f"https://twitter.com/i/oauth2/authorize?{query_string}"}

@router.get("/linkedin/url")
async def get_linkedin_auth_url(request: Request):
    client_id = os.getenv("LI_CLIENT_ID", "test-id")
    redirect_uri = get_redirect_uri(request)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "r_liteprofile r_emailaddress",
        "state": "linkedin"
    }
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return {"url": f"https://www.linkedin.com/oauth/v2/authorization?{query_string}"}

@router.get("/facebook/url")
async def get_facebook_auth_url(request: Request):
    client_id = os.getenv("FB_CLIENT_ID", "test-id")
    redirect_uri = get_redirect_uri(request)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "email,public_profile",
        "state": "facebook"
    }
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return {"url": f"https://www.facebook.com/v12.0/dialog/oauth?{query_string}"}


@router.post("/google/callback")
async def google_callback(request: Request):
    data = await request.json()
    code = data.get("code")

    if not code:
        return JSONResponse(status_code=400, content={"error": "Missing code"})

    # Dev bypass
    if code == "mock_code":
        return {"handle": "dev.analyst@market-rover.com", "name": "Dev Analyst", "provider": "Social Hub"}

    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": get_redirect_uri(request),
            "grant_type": "authorization_code"
        })
        tokens = token_res.json()

        if "error" in tokens:
            error_msg = f"OAUTH ERROR [{datetime.now()}]: {tokens.get('error_description', tokens.get('error'))}"
            logger.error(error_msg)
            return JSONResponse(status_code=400, content=tokens)

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        user_info = user_res.json()
        logger.info(f"AUTH SUCCESS: {user_info.get('email')}")
        return {
            "handle": user_info.get("email"),
            "name":   user_info.get("name"),
            "provider": "Google"
        }
