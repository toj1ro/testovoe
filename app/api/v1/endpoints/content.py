from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.content import ContentService
from app.models.content import Content, ContentCreate, ContentUpdate
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=Content)
async def create_content(
        content: ContentCreate,
        current_user: User = Depends(get_current_user),
) -> Any:
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания контента"
        )
    return await ContentService.create_content(content)


@router.get("/", response_model=List[Content])
async def get_content(
        current_user: User = Depends(get_current_user),
) -> Any:
    return await ContentService.get_content_by_roles(current_user.roles)


@router.get("/{content_id}", response_model=Content)
async def get_content_by_id(
        content_id: str,
        current_user: User = Depends(get_current_user),
) -> Any:
    content = await ContentService.get_content(content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )

    if not any(role in content.required_roles for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к контенту"
        )

    return content


@router.put("/{content_id}", response_model=Content)
async def update_content(
        content_id: str,
        content: ContentUpdate,
        current_user: User = Depends(get_current_user),
) -> Any:
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления контента"
        )

    updated_content = await ContentService.update_content(content_id, content)
    if not updated_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )
    return updated_content


@router.delete("/{content_id}")
async def delete_content(
        content_id: str,
        current_user: User = Depends(get_current_user),
) -> Any:
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления контента"
        )

    if not await ContentService.delete_content(content_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )
    return {"message": "Контент успешно удален"}
