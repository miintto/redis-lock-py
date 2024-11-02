class RedisLockError(Exception):
    """Base class for exceptions related to Redis locks"""


class InvalidArgsError(RedisLockError):
    pass


class LockNotOwnedError(RedisLockError):
    pass


class AcquireFailedError(RedisLockError):
    pass
