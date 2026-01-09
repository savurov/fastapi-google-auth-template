from fastapi import status
from httpx import AsyncClient

from src.core.security import AUTH_COOKIE_NAME
from src.users.models import User


async def test_me(auth_client: AsyncClient, db_user: User) -> None:
    response = await auth_client.get("/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert "email" in response.json()
    assert response.json()["email"] == db_user.email


async def test_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_me_invalid_jwt(client: AsyncClient) -> None:
    client.cookies.set(AUTH_COOKIE_NAME, "this-is-not-jwt-by-the-way")
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
