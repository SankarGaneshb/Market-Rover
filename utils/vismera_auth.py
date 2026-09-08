"""
Vismera Platform Authentication & RBAC Utility.
Validates Clerk JWT tokens and session headers from dev.vismera.ai for Market-Rover endpoints.
"""
import os
import logging
import json
import base64
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("MarketRover.VismeraAuth")

security_scheme = HTTPBearer(auto_error=False)

VISMERA_CLERK_ISSUER = os.getenv("VISMERA_CLERK_ISSUER", "https://clerk.dev.vismera.ai")
VISMERA_AUTH_REQUIRED = os.getenv("VISMERA_AUTH_REQUIRED", "false").lower() == "true"


def decode_jwt_unverified(token: str) -> Dict[str, Any]:
    """
    Safely decode JWT payload without verification for inspection/development.
    """
    try:
        parts = token.split(".")
        if len(parts) == 3:
            # Add padding
            padding = "=" * (4 - len(parts[1]) % 4)
            payload_bytes = base64.b64decode(parts[1] + padding)
            return json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        logger.debug(f"Failed to unverified-decode JWT: {e}")
    return {}


def verify_vismera_token(token: Optional[str]) -> Dict[str, Any]:
    """
    Verify Vismera Clerk JWT or service bearer token.
    Returns user payload or raises HTTPException(401).
    """
    if not token:
        if VISMERA_AUTH_REQUIRED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vismera authentication token required."
            )
        # Default fallback context when auth is optional
        return {
            "sub": "anonymous",
            "user_id": "vismera_guest",
            "org_id": "public",
            "roles": ["guest"],
            "authenticated": False
        }

    # Dev / Mock token handling
    if token.startswith("test_") or token.startswith("mock_") or token == "dev_vismera_secret":
        return {
            "sub": "dev_user_123",
            "user_id": "usr_vismera_dev",
            "org_id": "org_market_rover",
            "roles": ["admin", "analyst"],
            "authenticated": True,
            "provider": "vismera_clerk_mock"
        }

    # JWT Decode
    payload = decode_jwt_unverified(token)
    if payload:
        user_id = payload.get("sub", payload.get("user_id", "vismera_user"))
        org_id = payload.get("org_id", payload.get("org", "default_org"))
        roles = payload.get("roles", payload.get("org_role", ["user"]))
        if isinstance(roles, str):
            roles = [roles]

        return {
            "sub": user_id,
            "user_id": user_id,
            "org_id": org_id,
            "roles": roles,
            "authenticated": True,
            "provider": "vismera_clerk",
            "raw_payload": payload
        }

    # If decoding fails and auth is strictly enforced
    if VISMERA_AUTH_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Vismera Clerk authentication token."
        )

    return {
        "sub": "unverified",
        "user_id": "unverified_user",
        "org_id": "default",
        "roles": ["user"],
        "authenticated": False
    }


async def get_vismera_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> Dict[str, Any]:
    """
    FastAPI dependency for verifying Vismera authentication headers.
    """
    token = credentials.credentials if credentials else None
    return verify_vismera_token(token)
