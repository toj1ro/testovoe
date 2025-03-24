from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ContentBase(BaseModel):
    title: str
    description: str
    content: str
    required_roles: List[str]


class ContentCreate(ContentBase):
    pass


class ContentUpdate(ContentBase):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    required_roles: Optional[List[str]] = None


class Content(ContentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
