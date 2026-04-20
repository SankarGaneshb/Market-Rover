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

router = APIRouter()

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")


@router.get("/google/url")
async def get_google_auth_url():
    encoded_redirect = urllib.parse.quote(GOOGLE_REDIRECT_URI)
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={encoded_redirect}&scope=openid%20email%20profile"
        "&access_type=offline&prompt=select_account"
    )
    return {"url": url}


@router.post("/google/callback")
async def google_callback(request: Request):
    data = await request.json()
    code = data.get("code")

    if not code:
        return JSONResponse(status_code=400, content={"error": "Missing code"})

    # Dev bypass
    if code == "mock_code":
        return {"handle": "dev.analyst@market-rover.com", "name": "Dev Analyst", "provider": "Local"}

    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        })
        tokens = token_res.json()

        if "error" in tokens:
            return JSONResponse(status_code=400, content=tokens)

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        user_info = user_res.json()
        return {
            "handle": user_info.get("email"),
            "name":   user_info.get("name"),
            "provider": "Google"
        }
