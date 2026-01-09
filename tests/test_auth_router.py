from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import status
from httpx import AsyncClient, Response
from respx import Router
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import google_oauth
from src.auth.schemas import GoogleUser
from src.core.config import settings
from src.core.security import AUTH_COOKIE_NAME, OAUTH_STATE_COOKIE_NAME
from src.users.models import User
from tests.helpers import (
    assert_does_not_set_auth_cookie,
    assert_redirect,
    assert_redirect_to_error,
    assert_sets_auth_cookie,
    assert_state_cookie_deleted,
)


@pytest.fixture
def mock_id_token_validation(
    monkeypatch: pytest.MonkeyPatch, google_id_token_payload: dict[str, Any]
) -> None:
    def fake_verify(_token, _request, client_id) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        assert client_id == settings.google_client_id
        return google_id_token_payload

    monkeypatch.setattr(
        google_oauth.google_id_token,  # type: ignore[attr-defined]
        "verify_oauth2_token",
        fake_verify,
    )


async def test_logout(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/auth/logout")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert AUTH_COOKIE_NAME not in auth_client.cookies


async def test_google_login_redirect(client: AsyncClient) -> None:
    response = await client.get(
        "/auth/google/login",
    )

    assert response.status_code == status.HTTP_303_SEE_OTHER

    # cookie
    state = response.cookies.get(OAUTH_STATE_COOKIE_NAME)
    assert state is not None

    # location
    location = response.headers.get("location")
    parsed = urlparse(location)

    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"
    assert parsed.path == "/o/oauth2/v2/auth"

    # query
    actual_params = parse_qs(parsed.query)

    expected_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
        "state": state,
    }

    for key, value in expected_params.items():
        assert key in actual_params, f"Missing query param: {key}"
        assert len(actual_params[key]) == 1
        assert actual_params[key][0] == value


@pytest.mark.usefixtures("db_user", "mock_id_token_validation")
async def test_google_callback_existing_user(
    respx_mock: Router,
    client: AsyncClient,
    google_id_token: str,
) -> None:
    respx_mock.post(google_oauth.TOKEN_URL).return_value = Response(
        status.HTTP_200_OK, json={"id_token": google_id_token}
    )
    state = google_oauth.generate_token_state()
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state)

    response = await client.get(
        "/auth/google/callback",
        params={"code": "FAKE_CODE", "state": state},
    )

    assert_redirect(response)
    assert_sets_auth_cookie(response, client)


@pytest.mark.usefixtures("mock_id_token_validation")
async def test_google_callback_new_user(
    respx_mock: Router,
    session: AsyncSession,
    client: AsyncClient,
    google_user: GoogleUser,
    google_id_token: str,
) -> None:
    respx_mock.post(google_oauth.TOKEN_URL).return_value = Response(
        status.HTTP_200_OK, json={"id_token": google_id_token}
    )
    state = google_oauth.generate_token_state()
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state, domain="test.local")

    response = await client.get(
        "/auth/google/callback",
        params={"code": "FAKE_CODE", "state": state},
    )

    assert_redirect(response)
    assert_sets_auth_cookie(response, client)
    assert_state_cookie_deleted(response, client)

    stmt = select(User).where(User.google_id == google_user.sub)
    result = await session.execute(stmt)
    db_user = result.scalar_one_or_none()

    assert db_user is not None


async def test_google_callback_login_error(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/auth/google/callback",
        params={"error": "something_wrong"},
    )

    assert_redirect_to_error(response)
    assert_does_not_set_auth_cookie(response, client)
    assert_state_cookie_deleted(response, client)


async def test_google_callback_bad_google_response(
    respx_mock: Router,
    client: AsyncClient,
) -> None:
    respx_mock.post(google_oauth.TOKEN_URL).return_value = Response(
        status.HTTP_504_GATEWAY_TIMEOUT
    )

    state = google_oauth.generate_token_state()
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state, domain="test.local")

    response = await client.get(
        "/auth/google/callback",
        params={"code": "FAKE_CODE", "state": state},
    )

    assert_redirect_to_error(response)
    assert_does_not_set_auth_cookie(response, client)
    assert_state_cookie_deleted(response, client)


async def test_google_callback_invalid_state(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/auth/google/callback",
        params={"code": "FAKE_CODE", "state": "INVALID_STATE"},
    )

    assert_redirect_to_error(response)
    assert_does_not_set_auth_cookie(response, client)
    assert_state_cookie_deleted(response, client)


async def test_google_callback_invalid_id_token(
    monkeypatch: pytest.MonkeyPatch,
    respx_mock: Router,
    client: AsyncClient,
) -> None:
    def fake_verify(_token, _request, _client_id) -> None:  # type: ignore[no-untyped-def]
        raise ValueError("bad id_token")

    monkeypatch.setattr(
        google_oauth.google_id_token,  # type: ignore[attr-defined]
        "verify_oauth2_token",
        fake_verify,
    )

    respx_mock.post(google_oauth.TOKEN_URL).return_value = Response(
        status.HTTP_200_OK, json={"id_token": "FAKE_TOKEN"}
    )

    state = google_oauth.generate_token_state()
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, state, domain="test.local")

    response = await client.get(
        "/auth/google/callback",
        params={"code": "FAKE_CODE", "state": state},
    )

    assert_redirect_to_error(response)
    assert_does_not_set_auth_cookie(response, client)
    assert_state_cookie_deleted(response, client)


async def test_google_callback_missing_code(client: AsyncClient) -> None:
    response = await client.get("/auth/google/callback")

    assert_redirect_to_error(response)
    assert_does_not_set_auth_cookie(response, client)
    assert_state_cookie_deleted(response, client)
