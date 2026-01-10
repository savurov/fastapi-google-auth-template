from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserOut(BaseModel):
    id: UUID
    given_name: str
    family_name: str
    picture_url: str
    email: str
    created_at: datetime
