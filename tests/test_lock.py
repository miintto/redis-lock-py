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


class TestLock:
    def test_lock_arguments(self, redis: Redis):
        RedisLock(redis, name="key", blocking_timeout=1)
        RedisLock(redis, name="key", blocking_timeout=1.0)
        with pytest.raises(InvalidArgsError):
            RedisLock(redis, name=None)
        with pytest.raises(InvalidArgsError):
            RedisLock(redis, name="")
        with pytest.raises(InvalidArgsError):
            RedisLock(redis, name="key", blocking_timeout=None)
        with pytest.raises(InvalidArgsError):
            RedisLock(redis, name="key", blocking_timeout=-10)

        lock = RedisLock(redis, name="key")
        assert isinstance(lock.name, str)
        assert isinstance(lock.token, bytes)
        assert isinstance(lock.channel_name, str)

    def test_acquire_and_release(self, redis: Redis):
        name = "test_acquire_and_release"
        lock = RedisLock(redis, name)
        assert lock.acquire()
        assert lock.release()

    def test_acquire_with_context_manager(self, redis: Redis):
        name = "test_acquire_with_context_manager"
        with RedisLock(redis, name):
            assert redis.get(name)
        assert redis.get(name) is None

    def test_acquire_failed_error(self, redis: Redis):
        name = "test_acquire_failed_error"
        with RedisLock(redis, name):
            with pytest.raises(AcquireFailedError):
                with RedisLock(redis, name, blocking_timeout=.5):
                    pass
        redis.delete(name)

    def test_release_non_owned_lock_error(self, redis: Redis):
        name = "test_release_non_owned_lock_error"
        lock = RedisLock(redis, name)
        assert lock.acquire()
        redis.set(name, lock.token + b"foo")
        with pytest.raises(LockNotOwnedError):
            lock.release()
        redis.delete(name)

    def test_blocking_timeout(self, redis: Redis):
        name = "test_blocking_timeout"
        blocking_timeout = 1.0
        with RedisLock(redis, name):
            lock = RedisLock(redis, name, blocking_timeout=blocking_timeout)
            current = time.time()
            assert not lock.acquire()
            assert current + blocking_timeout < time.time()

    def test_pubsub_message(self, redis: Redis):
        name = "test_pubsub_message"
        lock = RedisLock(redis, name)

        def try_lock():
            another_lock = RedisLock(redis, name, blocking_timeout=1)
            assert another_lock.acquire()
            assert another_lock.release()

        lock.acquire()
        t = threading.Thread(target=try_lock)
        current = time.time()
        t.start()
        time.sleep(.5)
        lock.release()
        t.join()
        assert .5 < time.time() - current < 1

    def test_spin_lock(self, redis: Redis):
        name = "test_spin_lock"
        with RedisSpinLock(redis, name):
            assert redis.get(name)
        assert redis.get(name) is None

        with RedisSpinLock(redis, name):
            lock = RedisSpinLock(redis, name)
            assert not lock.acquire(blocking=False)

        with RedisSpinLock(redis, name):
            with pytest.raises(AcquireFailedError):
                with RedisSpinLock(redis, name, blocking_timeout=1):
                    pass

        lock = RedisSpinLock(redis, name)
        assert lock.acquire()
        redis.set(name, lock.token + b"foo")
        with pytest.raises(LockNotOwnedError):
            lock.release()
        redis.delete(name)
