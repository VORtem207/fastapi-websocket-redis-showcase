from pydantic import (
    BaseModel,
    EmailStr,
    constr,
)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserRegister(BaseModel):
    username: constr(min_length=3, max_length=30)
    email: EmailStr
    password: constr(min_length=8, max_length=30)
