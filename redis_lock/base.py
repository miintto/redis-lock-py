from abc import ABC, abstractmethod
from typing import Generic, Optional, Union
from uuid import uuid4

from redis import Redis
from redis_lock.exceptions import AcquireFailedError, InvalidArgsError
from redis_lock.types import RedisClient


class BaseLock(Generic[RedisClient], ABC):

    default_blocking_timeout = 60

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

    def __init__(
        self,
        client: RedisClient,
        name: Union[bytes, str],
        blocking_timeout: Union[int, float] = default_blocking_timeout,
        expire_timeout: Optional[int] = None,
    ):
        """Base Redis lock interface

        Args:
            client: A Redis client object.
            name: The name to be used as Redis key.
            blocking_timeout: The maximum blocking time in seconds to wait for
                a lock to be acquired.
            expire_timeout: The maximum lifetime of acquired lock.
        """
        self._client: RedisClient = client
        if not name:
            raise InvalidArgsError("A `name` argument should be required.")
        self._name = name
        self._uuid = uuid4().hex.encode()
        self._validate_timeout(blocking_timeout)
        self._blocking_timeout = float(blocking_timeout)
        self._ex = expire_timeout

    @property
    def name(self) -> str:
        return (
            self._name
            if isinstance(self._name, str)
            else self._name.decode("utf-8")
        )

    @property
    def token(self) -> bytes:
        return self._uuid

    @staticmethod
    def _validate_timeout(blocking_timeout: float):
        if not blocking_timeout:
            raise InvalidArgsError(
                "A `blocking_timeout` argument should be provided at the "
                "time of initializing the `Lock` class."
            )
        elif (
            not isinstance(blocking_timeout, (int, float))
            or blocking_timeout < 0
        ):
            raise InvalidArgsError(
                "A `blocking_timeout` argument should be integer of float and "
                "cannot be negative."
            )


class BaseSyncLock(BaseLock[Redis]):
    """Base Redis lock implementation"""

    def __enter__(self):
        if self.acquire():
            return self
        raise AcquireFailedError("Failed to acquire a lock.")

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    @abstractmethod
    def acquire(self, *args, **kwargs) -> bool:
        """Try to acquire a lock"""
        raise NotImplementedError(
            "The `acquire` method should be implemented!"
        )

    @abstractmethod
    def release(self) -> bool:
        """Release the owned lock"""
        raise NotImplementedError(
            "The `release` method should be implemented!"
        )
