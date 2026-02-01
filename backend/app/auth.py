import logging
from typing import Any

import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from urllib.parse import urlencode, quote

from .config import settings


class GoogleAuthError(Exception):
    pass


logger = logging.getLogger(__name__)


def verify_google_token(token: str) -> dict[str, Any]:
    if not settings.google_client_id:
        logger.error("GOOGLE_CLIENT_ID is not configured")
        raise GoogleAuthError("GOOGLE_CLIENT_ID is not configured")

    try:
        payload = id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.google_client_id
        )
    except Exception as exc:
        logger.exception("Google token verification failed")
        raise GoogleAuthError("Invalid Google token") from exc

    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "picture": payload.get("picture"),
    }


def exchange_code_for_token(code: str) -> dict[str, Any]:
    if not settings.google_client_id or not settings.google_client_secret:
        raise GoogleAuthError("Google client ID/secret not configured")
    if not settings.google_redirect_uri:
        raise GoogleAuthError("Google redirect URI not configured")

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    token_response.raise_for_status()
    return token_response.json()


def build_google_auth_url(state: str) -> str:
    if not settings.google_client_id:
        raise GoogleAuthError("GOOGLE_CLIENT_ID is not configured")
    if not settings.google_redirect_uri:
        raise GoogleAuthError("GOOGLE_REDIRECT_URI is not configured")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    query = urlencode(params, quote_via=quote)
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
