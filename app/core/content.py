import json
from datetime import datetime
from typing import List, Optional

from app.core.redis import redis_client
from app.models.content import Content, ContentCreate, ContentUpdate


class ContentService:
    @staticmethod
    async def create_content(content: ContentCreate) -> Content:
        content_id = f"content:{datetime.utcnow().timestamp()}"
        content_data = content.model_dump()
        content_data["id"] = content_id
        content_data["created_at"] = datetime.utcnow().isoformat()
        content_data["updated_at"] = datetime.utcnow().isoformat()

        redis_data = content_data.copy()
        redis_data["required_roles"] = json.dumps(redis_data["required_roles"])
        await redis_client.hmset(content_id, redis_data)

        return Content(**content_data)

    @staticmethod
    async def get_content(content_id: str) -> Optional[Content]:
        content_data = await redis_client.hgetall(content_id)
        if not content_data:
            return None

        content_data["required_roles"] = json.loads(content_data["required_roles"])
        return Content(**content_data)

    @staticmethod
    async def update_content(content_id: str, content: ContentUpdate) -> Optional[Content]:
        existing_content = await ContentService.get_content(content_id)
        if not existing_content:
            return None

        update_data = content.model_dump(exclude_unset=True)
        if "required_roles" in update_data:
            redis_data = update_data.copy()
            redis_data["required_roles"] = json.dumps(redis_data["required_roles"])
            redis_data["updated_at"] = datetime.utcnow().isoformat()
            await redis_client.hmset(content_id, redis_data)
        else:
            await redis_client.hset(content_id, "updated_at", datetime.utcnow().isoformat())

        return await ContentService.get_content(content_id)

    @staticmethod
    async def delete_content(content_id: str) -> bool:
        return bool(await redis_client.delete(content_id))

    @staticmethod
    async def get_all_content() -> List[Content]:
        content_keys = await redis_client.keys("content:*")
        contents = []
        for key in content_keys:
            content = await ContentService.get_content(key)
            if content:
                contents.append(content)
        return contents

    @staticmethod
    async def get_content_by_roles(user_roles: List[str]) -> List[Content]:
        all_content = await ContentService.get_all_content()
        accessible_content = []
        for content in all_content:
            if any(role in content.required_roles for role in user_roles):
                accessible_content.append(content)
        return accessible_content
