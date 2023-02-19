import pytest
import pytest_asyncio

from redis import Redis
from redis.asyncio import Redis as AsyncRedis


@pytest.fixture(scope="function")
def redis():
    return Redis(host="127.0.0.1", port=6379)


@pytest_asyncio.fixture(scope="function")
async def aredis():
    async with AsyncRedis(host="127.0.0.1", port=6379) as conn:
        yield conn
