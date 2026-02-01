import logging
from typing import Any

from google.auth.transport import requests
from google.oauth2 import id_token

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
            token, requests.Request(), settings.google_client_id
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
