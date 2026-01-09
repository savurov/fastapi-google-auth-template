import secrets

import httpx
from fastapi import status
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token as google_id_token
from starlette.datastructures import URL

from src.auth import schemas
from src.core.config import settings

TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"

google_request = requests.Request()


class OAuthFlowError(Exception):
    pass


def build_google_auth_url(state: str) -> URL:
    return URL(AUTH_BASE_URL).include_query_params(
        client_id=settings.google_client_id,
        redirect_uri=settings.google_redirect_uri,
        response_type="code",
        scope="openid email profile",
        prompt="select_account",
        state=state,
    )


def generate_token_state() -> str:
    return secrets.token_urlsafe(16)


def verify_id_token(token: str) -> schemas.GoogleUser:
    try:
        payload = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
            token,
            google_request,
            settings.google_client_id,
        )
    except (GoogleAuthError, ValueError) as exc:
        raise OAuthFlowError("id_token verification failed") from exc

    return schemas.GoogleUser.model_validate(payload)


async def fetch_id_token_from_code(code: str) -> str:
    payload = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url=TOKEN_URL, data=payload)
        if response.status_code != status.HTTP_200_OK:
            raise OAuthFlowError("Code to id_token exchange failed")
        return response.json()["id_token"]
