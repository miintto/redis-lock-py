from typing import TypeVar

from redis import Redis
from redis.asyncio import Redis as AsyncRedis


RedisClient = TypeVar("RedisClient", Redis, AsyncRedis)
