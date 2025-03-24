import json

from redis.asyncio import Redis

from app.core.config import settings
from app.models.user import UserInDB

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


class RedisService:
    @staticmethod
    async def add_to_whitelist(token_id: str, expire_time: int):
        await redis_client.set(f"whitelist:{token_id}", "1", ex=expire_time)

    @staticmethod
    async def add_to_blacklist(token_id: str, expire_time: int):
        await redis_client.set(f"blacklist:{token_id}", "1", ex=expire_time)

    @staticmethod
    async def is_token_blacklisted(token_id: str) -> bool:
        return bool(await redis_client.exists(f"blacklist:{token_id}"))

    @staticmethod
    async def is_token_whitelisted(token_id: str) -> bool:
        return bool(await redis_client.exists(f"whitelist:{token_id}"))

    @staticmethod
    async def store_user_session(user_id: str, session_data: dict):
        await redis_client.hmset(f"user:{user_id}:sessions", session_data)

    @staticmethod
    async def get_user_sessions(user_id: str) -> dict:
        return await redis_client.hgetall(f"user:{user_id}:sessions")

    @staticmethod
    async def store_user_roles(user_id: str, roles: list):
        await redis_client.sadd(f"user:{user_id}:roles", *roles)

    @staticmethod
    async def get_user_roles(user_id: str) -> set:
        return await redis_client.smembers(f"user:{user_id}:roles")

    @staticmethod
    async def create_user(user: UserInDB) -> bool:
        user_key = f"user:{user.id}"
        user_data = user.model_dump()

        user_data["is_active"] = str(user_data["is_active"]).lower()
        user_data["is_superuser"] = str(user_data["is_superuser"]).lower()

        user_data["roles"] = json.dumps(user_data["roles"])

        await redis_client.hmset(user_key, user_data)
        await redis_client.sadd("users:emails", user.email)
        await redis_client.set(f"user:email:{user.email}", user.id)
        return True

    @staticmethod
    async def get_user_by_email(email: str) -> UserInDB | None:
        user_id = await redis_client.get(f"user:email:{email}")
        if not user_id:
            return None

        user_key = f"user:{user_id}"
        user_data = await redis_client.hgetall(user_key)
        if not user_data:
            return None

        user_data["is_active"] = user_data["is_active"] == "true"
        user_data["is_superuser"] = user_data["is_superuser"] == "true"

        user_data["roles"] = json.loads(user_data["roles"])

        return UserInDB(**user_data)

    @staticmethod
    async def is_email_taken(email: str) -> bool:
        return await redis_client.sismember("users:emails", email)

    @staticmethod
    async def update_user_roles(user_id: str, roles: list) -> bool:
        user_key = f"user:{user_id}"
        user_data = await redis_client.hgetall(user_key)
        if not user_data:
            return False

        user_data["roles"] = json.dumps(roles)
        await redis_client.hmset(user_key, user_data)
        return True
