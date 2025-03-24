import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.redis import RedisService
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import Token, UserCreate, User, UserInDB, UserRolesUpdate

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    user = await RedisService.get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен"
        )

    access_token = create_access_token(
        subject=user.id,
        roles=user.roles
    )

    await RedisService.add_to_whitelist(
        user.id,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
        current_user: User = Depends(get_current_user),
) -> Any:
    await RedisService.add_to_blacklist(
        current_user.sub,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {"message": "Успешный выход из системы"}


@router.post("/register", response_model=User)
async def register(
        user_in: UserCreate,
) -> Any:
    if await RedisService.is_email_taken(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )

    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_in.password)

    user_db = UserInDB(
        id=user_id,
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        roles=["user"]
    )

    await RedisService.create_user(user_db)

    return User(
        id=user_id,
        email=user_in.email,
        username=user_in.username,
        is_active=True,
        is_superuser=False,
        roles=["user"]
    )


@router.put("/users/{user_id}/roles", response_model=User)
async def update_user_roles(
        user_id: str,
        roles_update: UserRolesUpdate,
        current_user: User = Depends(get_current_user),
) -> Any:
    if not await RedisService.update_user_roles(user_id, roles_update.roles):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    user = await RedisService.get_user_by_email(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    return User(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=user.roles
    )
