# Redis Lock with PubSub

Redis distributed lock implementation for Python base on Pub/Sub messaging.

## 1. Features

- SETNX를 통한 원자성 보장
- Pub/Sub 시스템으로 message를 받은 경우만 락 획득 재시도
- Timeout을 강제하여 무한 대기 방지

동시성 이슈 해결이 필요한 경우 분산 락(distributed lock) 구현체로 활용할 수 있습니다.
기존 [redis-py](https://github.com/redis/redis-py)에 내장된 spin lock 대신 Pub/Sub 방식을 적용하여 서버의 부하를 최소화 하였습니다.

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

기본적인 사용 예제입니다.
커넥션으로 [redis-py](https://github.com/redis/redis-py) 클라이언트 객체를 활용하였습니다.
`RedisLock.acquire` 메소드를 호출하여 락을 획득한 경우 결과로 참을 반환하는데, 해당 경우 주어진 작업을 진행한 후 `RedisLock.release`를 호출하여 락을 반환합니다.

### 3.2 Using Context Managers

```python
import redis
from redis_lock import RedisLock

client = redis.Redis(host="127.0.0.1", port=6379)

with RedisLock(client, "foo", blocking_timeout=10):
    print("Acquired lock successfully!")
```

성공적으로 락을 획득하였지만 다시 락을 반환하는 부분이 누락된다면 이후 동일한 `name`으로 접근하는 다른 클라이언트들은 모두 락을 획득하지 못할 수 있습니다.
이런 경우를 미연에 방지하고자 `with` 구문이 끝날 때 락을 해제하도록 프로그래밍적으로 강제하였습니다.
두 예시 **2.1**, **2.2** 코드는 모두 동일하게 동작합니다.

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

Spin lock도 사용 가능합니다.
기본적인 동작 방식은 비슷하지만 `RedisSpinLock.acquire` 메소드에서 추가적으로 blocking 여부와 sleep time을 입력받습니다.
특별한 이유가 없다면 `RedisLock` 사용을 권장드립니다.

### System Flow

![redis-lock-flow](https://user-images.githubusercontent.com/37063580/215324117-ff55fc4e-cc14-42c1-8628-e472adf8b865.png)

