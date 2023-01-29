from typing import Union

from redis import Redis
from redis.asyncio import Redis as AsyncRedis


RedisClient = Union[Redis, AsyncRedis]
LockKey = Union[bytes, str]
TimeOutType = Union[float, int]
