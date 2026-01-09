from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.core.config import settings
from src.core.db import reinit_database
from src.users.router import router as users_router

API_PREFIX = "/v1"


@asynccontextmanager  # pragma: no cover
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.reset_db_on_startup:
        await reinit_database()
    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix=API_PREFIX)
router.include_router(users_router)
router.include_router(auth_router)

app.include_router(router)
