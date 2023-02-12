[![License](https://img.shields.io/badge/license-MIT-lightgray.svg)](./LICENSE)
[![PyPI Release](https://img.shields.io/pypi/v/redis-lock-py)](https://pypi.org/project/redis-lock-py/)
![Python Support](https://img.shields.io/pypi/pyversions/redis-lock-py)
![Implementation](https://img.shields.io/pypi/implementation/redis-lock-py.svg)

# Redis Lock with PubSub

Redis distributed lock implementation for Python based on Pub/Sub messaging.

## 1. Features

- Ensure atomicity by using SETNX operation
- Pub/Sub messaging system between the client waiting to get the lock and holding the lock
- Force timeout to avoid infinite loops when trying to acquire lock
- Async is supported

## 2. Installation

```bash
$> pip install redis-lock-py
```

### Dependencies
- Python >= 3.7
- redis-py >= 4.2.0

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

[redis-py](https://github.com/redis/redis-py) library is required for redis connection objects.
The `RedisLock.release` method must be invoked to release the lock after acquiring a lock successfully by calling `RedisLock.acquire` method with returned `True`.

### 3.2 Using Context Managers

```python
import redis
from redis_lock import RedisLock

client = redis.Redis(host="127.0.0.1", port=6379)

with RedisLock(client, "foo", blocking_timeout=10):
    print("Acquired lock successfully!")
```

If the part that releases the lock is missing after acquire a lock, 
all the clients that access the same `name` may not be able to acquire the lock.
To prevent this unexpected malfunction from happening, programmed to unlock the lock by itself at the end of the `with` context.
Both examples in **3.1** and **3.2** work the same way.

### 3.3 Using Spin Lock

```python
import redis
from redis_lock import RedisSpinLock

client = redis.Redis(host="127.0.0.1", port=6379)

lock = RedisSpinLock(client, "foo")
if not lock.acquire(blocking=True, sleep_time=0.1):
    raise Exception("Fail to acquire lock")
print("Acquired lock successfully!")
lock.release()
```

Spin lock is also available,
but not recommended unless there is a compelling reason to use them because of inefficiency compare to the Pub/Sub messaging system.

### System Flow

![redis-lock-flow](https://user-images.githubusercontent.com/37063580/215324117-ff55fc4e-cc14-42c1-8628-e472adf8b865.png)

