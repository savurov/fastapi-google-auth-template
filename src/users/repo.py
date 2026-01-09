from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import schemas
from src.core.db import SessionDep
from src.users.models import User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> User:
        stmt = select(User).where(User.id == id)

        result = await self.session.execute(stmt)
        user = result.scalar_one()

        return user

    async def update_or_create_google_user(self, g_user: schemas.GoogleUser) -> User:
        stmt = (
            insert(User)
            .values(
                google_id=g_user.sub,
                email=g_user.email,
                given_name=g_user.given_name,
                family_name=g_user.family_name,
                picture_url=g_user.picture,
            )
            .on_conflict_do_update(
                index_elements=[User.google_id],
                set_={
                    "email": g_user.email,
                    "given_name": g_user.given_name,
                    "family_name": g_user.family_name,
                    "picture_url": g_user.picture,
                },
            )
            .returning(User)
        )

        result = await self.session.execute(stmt)
        user = result.scalar_one()
        await self.session.commit()
        return user


def get_user_repo(session: SessionDep) -> UserRepo:
    return UserRepo(session)


UserRepoDep = Annotated[UserRepo, Depends(get_user_repo)]
