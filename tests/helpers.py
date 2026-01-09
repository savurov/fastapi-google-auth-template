from fastapi import status
from httpx import AsyncClient, Response

from src.core.config import settings
from src.core.security import AUTH_COOKIE_NAME, OAUTH_STATE_COOKIE_NAME


def assert_redirect(response: Response) -> None:
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == settings.frontend_url


def assert_redirect_to_error(response: Response) -> None:
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"].startswith(settings.frontend_oauth_error_url)


def assert_sets_auth_cookie(response: Response, client: AsyncClient) -> None:
    set_cookie = response.headers.get("set-cookie", "")
    assert AUTH_COOKIE_NAME in set_cookie
    assert client.cookies.get(AUTH_COOKIE_NAME) is not None


def assert_does_not_set_auth_cookie(response: Response, client: AsyncClient) -> None:
    set_cookie = response.headers.get("set-cookie", "")
    assert AUTH_COOKIE_NAME not in set_cookie
    assert client.cookies.get(AUTH_COOKIE_NAME) is None


def assert_state_cookie_deleted(response: Response, client: AsyncClient) -> None:
    set_cookie = response.headers.get("set-cookie", "")
    assert OAUTH_STATE_COOKIE_NAME in set_cookie
    assert client.cookies.get(OAUTH_STATE_COOKIE_NAME) is None
