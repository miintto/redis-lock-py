[![License](https://img.shields.io/badge/license-MIT-lightgray.svg)](./LICENSE)
[![PyPI Release](https://img.shields.io/pypi/v/redis-lock-py)](https://pypi.org/project/redis-lock-py/)
[![Downloads](https://static.pepy.tech/badge/redis-lock-py)](https://pepy.tech/project/redis-lock-py)
![Python Support](https://img.shields.io/pypi/pyversions/redis-lock-py)
![Implementation](https://img.shields.io/pypi/implementation/redis-lock-py.svg)
[![codecov](https://codecov.io/gh/miintto/redis-lock-py/branch/master/graph/badge.svg?token=I9A9JKIWKF)](https://codecov.io/gh/miintto/redis-lock-py)

# Redis Lock with PubSub

Redis distributed lock implementation for Python based on Pub/Sub messaging.

## 1. Features

- Ensure atomicity by using the SETNX operation.
- Implements a Pub/Sub messaging system between the client attempting to acquire the lock and the one currently holding it.
- Includes a forced timeout mechanism to prevent infinite loops when attempting to acquire the lock.
- Supports asynchronous operations.

## 2. Installation

```bash
$> pip install redis-lock-py
```

### Dependencies
- Python >= 3.9
- redis-py >= 5.2.0

## 3. Usage

### 3.1 Basic Example

```python
import redis
from redis_lock import RedisLock

client = redis.Redis(host="127.0.0.1", port=6379)

name = "foo"
lock = RedisLock(client, name)
if not lock.acquire():
    raise Exception("Fail to acquire lock")
print("Acquired lock successfully!")
lock.release()
```

The [redis-py](https://github.com/redis/redis-py) library is required for Redis connection objects.
After successfully acquiring the lock using `RedisLock.acquire`, ensure to release it by calling `RedisLock.release` to prevent lock retention.

### 3.2 Using Context Managers

```python
import redis
from redis_lock import RedisLock

client = redis.Redis(host="127.0.0.1", port=6379)

with RedisLock(client, name="foo", blocking_timeout=10):
    print("Acquired lock successfully!")
```

To avoid issues where the lock remains unreleased (potentially blocking other clients from acquiring it),
you can use `RedisLock` with a context manager, which ensures that the lock is automatically released at the end of the `with` block.
Both examples in sections **3.1** and **3.2** function in a same manner.

### 3.3 With Asyncio

```python
from redis.asyncio import Redis
from redis_lock.asyncio import RedisLock

client = Redis(host="127.0.0.1", port=6379)

async with RedisLock(client, name="foo", blocking_timeout=10):
    print("Acquired lock successfully!")
```

**redis-lock** supports the asyncio platform.

### 3.4 Using Spin Lock

```python
import redis
from redis_lock import RedisSpinLock

client = redis.Redis(host="127.0.0.1", port=6379)

lock = RedisSpinLock(client, name="foo")
if not lock.acquire(blocking=True, sleep_time=0.1):
    raise Exception("Fail to acquire lock")
print("Acquired lock successfully!")
lock.release()
```

While a spin lock is available,
it is not recommended unless there is a compelling reason to use it, as it is less efficient compared to the Pub/Sub messaging system.

### System Flow

![redis-lock-flow](https://user-images.githubusercontent.com/37063580/215324117-ff55fc4e-cc14-42c1-8628-e472adf8b865.png)

