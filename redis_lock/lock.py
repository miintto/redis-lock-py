import time

from redis import Redis
from redis.client import PubSub

from redis_lock.base import BaseLock
from redis_lock.exceptions import LockNotOwnedError
from redis_lock.types import LockKey


class RedisLock(BaseLock):

    unlock_message = b"ok"

    # keys: (Lock.name, Lock.channel_name)
    # args (Lock.token, Lock.unlock_message)
    LUA_RELEASE = """
        if redis.call("GET", KEYS[1]) ~= ARGV[1] then
            return 0
        end
        redis.call("DEL", KEYS[1])
        redis.call("PUBLISH", KEYS[2], ARGV[2]);
        return 1
    """

    def __init__(self, client: Redis, name: LockKey, *args, **kwargs):
        super().__init__(client, name, *args, **kwargs)
        self.lua_release = self._client.register_script(self.LUA_RELEASE)

    @property
    def channel_name(self) -> str:
        return f"rlock-channel:{self.name}"

    def _try_acquire(self) -> bool:
        if self._client.set(self.name, self.token, nx=True, ex=self._ex):
            return True
        return False

    def _subscribe_channel(self, pubsub: PubSub):
        if not pubsub.subscribed:
            pubsub.subscribe(self.channel_name)

    def _wait_for_message(self, pubsub: PubSub, timeout: int) -> bool:
        break_time = time.time() + timeout
        while True:
            message = pubsub.get_message(
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

    def acquire(self) -> bool:
        """Try to acquire a lock

        Returns:
            bool: `True` if the lock was acquired, `False` otherwise.
        """
        timeout = self._blocking_timeout
        if self._try_acquire():
            return True

        with self._client.pubsub() as pubsub:
            self._subscribe_channel(pubsub)
            stop_trying_at = time.time() + timeout
            while True:
                self._wait_for_message(pubsub, timeout=timeout)
                if stop_trying_at < time.time():
                    return False
                elif self._try_acquire():
                    return True

    def release(self) -> bool:
        """Release the owned lock

        Returns:
            bool: `True` if the lock was successfully released,
                `False` otherwise.
        """
        if not self.lua_release(
            keys=(self.name, self.channel_name),
            args=(self.token, self.unlock_message),
        ):
            raise LockNotOwnedError("Unable to release non-owned lock.")
        return True
