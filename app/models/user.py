from typing import Optional, List

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDB(UserBase):
    id: str
    hashed_password: str
    roles: List[str] = []

    class Config:
        from_attributes = True


class User(UserBase):
    id: str
    roles: List[str] = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str
    exp: int
    roles: List[str] = []


class UserRolesUpdate(BaseModel):
    roles: List[str]
