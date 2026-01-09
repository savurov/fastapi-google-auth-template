from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from src.auth.schemas import GoogleUser
from src.core.config import settings
from src.core.db import Base, get_session
from src.core.security import (
    AUTH_COOKIE_NAME,
    create_access_token,
)
from src.main import API_PREFIX, app
from src.users.models import User


@pytest.fixture(scope="session", autouse=True)
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(settings.test_database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def reinit_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f"http://test{API_PREFIX}",
        follow_redirects=False,
    ) as c:
        yield c

    app.dependency_overrides = {}


@pytest.fixture
def faker() -> Faker:
    return Faker()


@pytest.fixture
def google_user(faker: Faker) -> GoogleUser:
    return GoogleUser(
        sub=faker.numerify(text="#" * 21),
        email=faker.email(),
        given_name=faker.first_name(),
        family_name=faker.last_name(),
        picture=faker.image_url(),
    )


@pytest.fixture
async def db_user(session: AsyncSession, google_user: GoogleUser) -> User:
    new_user = User(
        google_id=google_user.sub,
        email=google_user.email,
        given_name=google_user.given_name,
        family_name=google_user.family_name,
        picture_url=google_user.picture,
    )
    session.add(new_user)
    await session.flush()
    return new_user


@pytest.fixture
def google_id_token_payload(
    google_user: GoogleUser,
) -> dict[str, Any]:
    return {
        "sub": google_user.sub,
        "email": google_user.email,
        "given_name": google_user.given_name,
        "family_name": google_user.family_name,
        "picture": google_user.picture,
        "exp": datetime.now(UTC) + timedelta(minutes=1),
        "aud": settings.google_client_id,
    }


@pytest.fixture
def google_id_token(google_id_token_payload: dict[str, Any]) -> str:
    return jwt.encode(google_id_token_payload, key="", algorithm="none")


@pytest.fixture
async def auth_client(client: AsyncClient, db_user: User) -> AsyncClient:
    access_token = create_access_token(db_user.id)
    client.cookies.set(AUTH_COOKIE_NAME, access_token, domain="test.local")
    return client
