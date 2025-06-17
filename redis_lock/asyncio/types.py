from datetime import timedelta
from typing import Union

from redis.asyncio import Redis as AsyncRedis

RedisClient = AsyncRedis
LockKey = Union[bytes, str]
TimeOutType = Union[int, timedelta]
