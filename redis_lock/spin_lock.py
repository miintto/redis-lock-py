import time

from redis_lock.base import BaseSyncLock
from redis_lock.exceptions import LockNotOwnedError


class RedisSpinLock(BaseSyncLock):

    # keys: (Lock.name,)
    # args (Lock.token,)
    LUA_RELEASE = """
        if redis.call("GET", KEYS[1]) ~= ARGV[1] then
            return 0
        end
        redis.call("DEL", KEYS[1])
        return 1
    """

    def acquire(self, blocking: bool = True, sleep_time: float = 0.1) -> bool:
        """Try to acquire a lock

        Args:
            blocking: If `True`, wait for the lock to be acquired. If not,
                return the results immediately.
            sleep_time: The sleep time in seconds to wait for the next
                iteration if the lock is not accessible.

        Returns:
           bool: `True` if the lock was acquired, `False` otherwise.
        """
        timeout = self._blocking_timeout

        while True:
            current = time.time()
            if self._client.set(self.name, self.token, nx=True, ex=self._ex):
                return True
            elif not blocking:
                return False
            time.sleep(sleep_time)
            timeout -= (time.time() - current)
            if timeout < 0:
                return False

    def release(self) -> bool:
        """Release the owned lock

        Returns:
            bool: `True` if the lock was successfully released,
                `False` otherwise.
        """
        if not self.lua_release(keys=(self.name,), args=(self.token,)):
            raise LockNotOwnedError("Unable to release non-owned lock.")
        return True
