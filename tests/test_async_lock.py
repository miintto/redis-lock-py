import asyncio
import time

import pytest
from redis.asyncio import Redis

from redis_lock.asyncio import RedisLock
from redis_lock.exceptions import (
    AcquireFailedError,
    InvalidArgsError,
    LockNotOwnedError,
)


class TestAsyncLock:
    @pytest.mark.asyncio
    async def test_lock_arguments(self, aredis: Redis):
        RedisLock(aredis, name="key", blocking_timeout=1)
        RedisLock(aredis, name="key", blocking_timeout=1.0)
        with pytest.raises(InvalidArgsError):
            RedisLock(aredis, name=None)
        with pytest.raises(InvalidArgsError):
            RedisLock(aredis, name="")
        with pytest.raises(InvalidArgsError):
            RedisLock(aredis, name="key", blocking_timeout=None)
        with pytest.raises(InvalidArgsError):
            RedisLock(aredis, name="key", blocking_timeout=-10)

        lock = RedisLock(aredis, name="key")
        assert isinstance(lock.name, str)
        assert isinstance(lock.token, bytes)
        assert isinstance(lock.channel_name, str)

    @pytest.mark.asyncio
    async def test_acquire_and_release(self, aredis: Redis):
        name = "async_test_acquire_and_release"
        lock = RedisLock(aredis, name)
        assert await lock.acquire()
        assert await lock.release()

    @pytest.mark.asyncio
    async def test_acquire_with_context_manager(self, aredis: Redis):
        name = "async_test_acquire_with_context_manager"
        async with RedisLock(aredis, name):
            assert await aredis.get(name)
        assert await aredis.get(name) is None

    @pytest.mark.asyncio
    async def test_acquire_failed_error(self, aredis: Redis):
        name = "async_test_acquire_failed_error"
        async with RedisLock(aredis, name):
            with pytest.raises(AcquireFailedError):
                async with RedisLock(aredis, name, blocking_timeout=.5):
                    pass
        await aredis.delete(name)

    @pytest.mark.asyncio
    async def test_release_non_owned_lock_error(self, aredis: Redis):
        name = "async_test_release_non_owned_lock_error"
        lock = RedisLock(aredis, name)
        assert await lock.acquire()
        await aredis.set(name, lock.token + b"foo")
        with pytest.raises(LockNotOwnedError):
            await lock.release()
        await aredis.delete(name)

    @pytest.mark.asyncio
    async def test_blocking_timeout(self, aredis: Redis):
        name = "async_test_blocking_timeout"
        blocking_timeout = 1.0
        async with RedisLock(aredis, name):
            lock = RedisLock(aredis, name, blocking_timeout=blocking_timeout)
            current = time.time()
            assert not await lock.acquire()
            assert current + blocking_timeout < time.time()

    @pytest.mark.asyncio
    async def test_pubsub_message(self, aredis: Redis):
        name = "async_test_pubsub_message"
        lock = RedisLock(aredis, name)

        async def try_lock():
            another_lock = RedisLock(aredis, name, blocking_timeout=1)
            assert await another_lock.acquire()
            assert await another_lock.release()

        async def release_lock():
            await asyncio.sleep(.5)
            await lock.release()

        await lock.acquire()
        current = time.time()
        await asyncio.gather(
            asyncio.create_task(try_lock()),
            asyncio.create_task(release_lock()),
        )
        assert .5 < time.time() - current < 1
