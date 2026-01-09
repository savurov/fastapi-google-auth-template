from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import HTTPException, Response, status

from src.core.config import settings

AUTH_COOKIE_NAME = "access_token"
OAUTH_STATE_COOKIE_NAME = "oauth_state"

auth_failed_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed",
)


def create_access_token(user_id: UUID) -> str:
    expires_delta = timedelta(minutes=settings.cookie_expire_minutes)
    expire = datetime.now(UTC) + expires_delta

    encoded_jwt = jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.secret_key,
        algorithm="HS256",
    )
    return encoded_jwt


def get_user_id_from_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")


def set_auth_cookie(response: Response, user_id: UUID) -> None:
    token = create_access_token(user_id)

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.is_production,
        max_age=60 * settings.cookie_expire_minutes,
    )


def delete_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.is_production,
    )


def set_oauth_state_cookie(response: Response, state: str) -> None:
    response.set_cookie(
        OAUTH_STATE_COOKIE_NAME,
        state,
        httponly=True,
        secure=settings.is_production,
        max_age=600,
    )


def delete_oauth_state_cookie(response: Response) -> None:
    response.delete_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        httponly=True,
        secure=settings.is_production,
        path="/",
    )
