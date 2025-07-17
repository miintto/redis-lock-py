from abc import abstractmethod

from redis.asyncio import Redis

from redis_lock.base import BaseLock
from redis_lock.exceptions import AcquireFailedError


class BaseAsyncLock(BaseLock[Redis]):
    """Base Redis lock implementation for asyncio"""

    async def __aenter__(self):
        if await self.acquire():
            return self
        raise AcquireFailedError("Failed to acquire a lock.")

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.release()

    @abstractmethod
    async def acquire(self, *args, **kwargs) -> bool:
        """Try to acquire a lock"""
        raise NotImplementedError(
            "The `acquire` method should be implemented!"
        )

    @abstractmethod
    async def release(self) -> bool:
        """Release the owned lock"""
        raise NotImplementedError(
            "The `release` method should be implemented!"
        )
