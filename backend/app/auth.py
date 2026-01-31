from typing import Any

from google.auth.transport import requests
from google.oauth2 import id_token

from .config import settings


class GoogleAuthError(Exception):
    pass


def verify_google_token(token: str) -> dict[str, Any]:
    if not settings.google_client_id:
        raise GoogleAuthError("GOOGLE_CLIENT_ID is not configured")

    try:
        payload = id_token.verify_oauth2_token(
            token, requests.Request(), settings.google_client_id
        )
    except Exception as exc:
        raise GoogleAuthError("Invalid Google token") from exc

    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "picture": payload.get("picture"),
    }
