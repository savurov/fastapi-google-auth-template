from pydantic import BaseModel


class GoogleUser(BaseModel, extra="ignore"):
    sub: str
    email: str
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
