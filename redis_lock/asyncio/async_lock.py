import time

from redis.asyncio.client import PubSub

from redis_lock.asyncio.base import BaseAsyncLock
from redis_lock.exceptions import LockNotOwnedError


class RedisLock(BaseAsyncLock):

    @property
    def channel_name(self) -> str:
        return f"rlock-channel:{self.name}"

    async def _try_acquire(self) -> bool:
        if await self._client.set(self.name, self.token, nx=True, ex=self._ex):
            return True
        return False

    async def _subscribe_channel(self, pubsub: PubSub):
        if not pubsub.subscribed:
            await pubsub.subscribe(self.channel_name)

    async def _wait_for_message(self, pubsub: PubSub, timeout: int) -> bool:
        break_time = time.time() + timeout
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=timeout
            )
            if not message and break_time < time.time():
                return False
            elif (
                message
                and message["type"] == "message"
                and message["data"] == self.unlock_message
            ):
                return True

    async def acquire(self) -> bool:
        """Try to acquire a lock

        Returns:
            bool: `True` if the lock was acquired, `False` otherwise.
        """
        timeout = self._blocking_timeout
        if await self._try_acquire():
            return True

        async with self._client.pubsub() as pubsub:
            await self._subscribe_channel(pubsub)
            stop_trying_at = time.time() + timeout
            while True:
                await self._wait_for_message(pubsub, timeout=timeout)
                if stop_trying_at < time.time():
                    return False
                elif await self._try_acquire():
                    return True

    async def release(self) -> bool:
        """Release the owned lock

        Returns:
            bool: `True` if the lock was successfully released,
                `False` otherwise.
        """
        if not await self.lua_release(
            keys=(self.name, self.channel_name),
            args=(self.token, self.unlock_message),
        ):
            raise LockNotOwnedError("Unable to release non-owned lock.")
        return True
