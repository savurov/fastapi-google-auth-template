import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    google_id: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column()
    given_name: Mapped[str | None] = mapped_column()
    family_name: Mapped[str | None] = mapped_column()
    picture_url: Mapped[str | None] = mapped_column()

    is_admin: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
