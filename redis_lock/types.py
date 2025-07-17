from typing import Optional, Union, TypeVar

from redis import Redis
from redis.asyncio import Redis as AsyncRedis


RedisClient = TypeVar("RedisClient", Redis, AsyncRedis)

LockKey = Union[bytes, str]
TimeOutType = Optional[int]
