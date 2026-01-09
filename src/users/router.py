from typing import Any

from fastapi import APIRouter

from src.core.deps import CurrentUserDep
from src.users import schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=schemas.UserOut,
    summary="Get current user",
)
async def read_current_user(current_user: CurrentUserDep) -> Any:
    return current_user
