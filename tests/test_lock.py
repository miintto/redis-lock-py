import threading
import time

import pytest
from redis import Redis

from redis_lock import RedisLock, RedisSpinLock
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


def test_acquire_and_release(redis_client):
    name = "test_acquire_and_release"
    lock = RedisLock(redis_client, name)
    assert lock.acquire()
    assert lock.release()


def test_acquire_with_context_manager(redis_client):
    name = "test_acquire_with_context_manager"
    with RedisLock(redis_client, name):
        assert redis_client.get(name)
    assert redis_client.get(name) is None


def test_acquire_failed_error(redis_client):
    name = "test_acquire_failed_error"
    with RedisLock(redis_client, name):
        with pytest.raises(AcquireFailedError):
            with RedisLock(redis_client, name, blocking_timeout=.5):
                pass
    redis_client.delete(name)


def test_release_non_owned_lock_error(redis_client):
    name = "test_release_non_owned_lock_error"
    lock = RedisLock(redis_client, name)
    assert lock.acquire()
    redis_client.set(name, lock.token + b"foo")
    with pytest.raises(LockNotOwnedError):
        lock.release()
    redis_client.delete(name)


def test_blocking_timeout(redis_client):
    name = "test_blocking_timeout"
    blocking_timeout = 1.0
    with RedisLock(redis_client, name):
        lock = RedisLock(redis_client, name, blocking_timeout=blocking_timeout)
        current = time.time()
        assert not lock.acquire()
        assert current + blocking_timeout < time.time()


def test_pubsub_message(redis_client):
    name = "test_pubsub_message"
    lock = RedisLock(redis_client, name)

    def try_lock():
        l = RedisLock(redis_client, name, blocking_timeout=1)
        assert l.acquire()
        assert l.release()

    lock.acquire()
    t = threading.Thread(target=try_lock)
    current = time.time()
    t.start()
    time.sleep(.5)
    lock.release()
    t.join()
    assert .5 < time.time() - current < 1


def test_spin_lock(redis_client):
    name = "test_spin_lock"
    with RedisSpinLock(redis_client, name):
        assert redis_client.get(name)
    assert redis_client.get(name) is None

    with RedisSpinLock(redis_client, name):
        lock = RedisSpinLock(redis_client, name)
        assert not lock.acquire(blocking=False)

    with RedisSpinLock(redis_client, name):
        with pytest.raises(AcquireFailedError):
            with RedisSpinLock(redis_client, name, blocking_timeout=1):
                pass

    lock = RedisSpinLock(redis_client, name)
    assert lock.acquire()
    redis_client.set(name, lock.token + b"foo")
    with pytest.raises(LockNotOwnedError):
        lock.release()
    redis_client.delete(name)
