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


@pytest.fixture
def redis_client():
    return Redis(host="127.0.0.1", port=6379)


def test_lock_arguments(redis_client):
    RedisLock(redis_client, name="key", blocking_timeout=1)
    RedisLock(redis_client, name="key", blocking_timeout=1.0)
    with pytest.raises(InvalidArgsError):
        RedisLock(redis_client, name=None)
    with pytest.raises(InvalidArgsError):
        RedisLock(redis_client, name="")
    with pytest.raises(InvalidArgsError):
        RedisLock(redis_client, name="key", blocking_timeout=None)
    with pytest.raises(InvalidArgsError):
        RedisLock(redis_client, name="key", blocking_timeout=-10)

    lock = RedisLock(redis_client, name="key")
    assert isinstance(lock.name, str)
    assert isinstance(lock.token, bytes)
    assert isinstance(lock.channel_name, str)


@pytest.mark.asyncio
async def test_acquire_and_release(redis_client):
    name = "async_test_acquire_and_release"
    lock = RedisLock(redis_client, name)
    assert await lock.acquire()
    assert await lock.release()


@pytest.mark.asyncio
async def test_acquire_with_context_manager(redis_client):
    name = "async_test_acquire_with_context_manager"
    async with RedisLock(redis_client, name):
        assert await redis_client.get(name)
    assert await redis_client.get(name) is None


@pytest.mark.asyncio
async def test_acquire_failed_error(redis_client):
    name = "async_test_acquire_failed_error"
    async with RedisLock(redis_client, name):
        with pytest.raises(AcquireFailedError):
            async with RedisLock(redis_client, name, blocking_timeout=.5):
                pass
    await redis_client.delete(name)


@pytest.mark.asyncio
async def test_release_non_owned_lock_error(redis_client):
    name = "async_test_release_non_owned_lock_error"
    lock = RedisLock(redis_client, name)
    assert await lock.acquire()
    await redis_client.set(name, lock.token + b"foo")
    with pytest.raises(LockNotOwnedError):
        await lock.release()
    await redis_client.delete(name)


@pytest.mark.asyncio
async def test_blocking_timeout(redis_client):
    name = "async_test_blocking_timeout"
    blocking_timeout = 1.0
    async with RedisLock(redis_client, name):
        lock = RedisLock(redis_client, name, blocking_timeout=blocking_timeout)
        current = time.time()
        assert not await lock.acquire()
        assert current + blocking_timeout < time.time()


@pytest.mark.asyncio
async def test_pubsub_message(redis_client):
    name = "async_test_pubsub_message"
    lock = RedisLock(redis_client, name)

    async def try_lock():
        l = RedisLock(redis_client, name, blocking_timeout=1)
        assert await l.acquire()
        assert await l.release()

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
