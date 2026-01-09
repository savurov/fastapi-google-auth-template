from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from src.core import security
from src.users.models import User
from src.users.repo import UserRepoDep

auth_failed_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed",
)


async def get_current_user_id(request: Request) -> UUID:
    token = request.cookies.get(security.AUTH_COOKIE_NAME)
    if not token:
        raise auth_failed_exception

    user_id = security.get_user_id_from_token(token)
    if user_id is None:
        raise auth_failed_exception

    return user_id


CurrentUserIdDep = Annotated[UUID, Depends(get_current_user_id)]


async def get_current_user(user_repo: UserRepoDep, user_id: CurrentUserIdDep) -> User:
    user = await user_repo.get_by_id(id=user_id)
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
