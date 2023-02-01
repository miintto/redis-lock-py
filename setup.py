import re
from setuptools import find_packages, setup
from typing import List


def get_version() -> str:
    with open("redis_lock/__init__.py", "r") as f:
        pattern = r"__version__ = \"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\""
        version = re.findall(pattern, f.read())
        return version[0]


def get_requirements(filename: str) -> List:
    with open(filename, "r") as f:
        lines = f.readlines()
    return [line.strip() for line in lines]


setup(
    name="redis-lock-py",
    version=get_version(),
    license="MIT",
    author="Minjae Park",
    author_email="miintto.log@google.com",
    description="Redis distributed lock implementation for Python "
                "base on Pub/Sub messaging",
    long_description=open("README.md").read().strip(),
    long_description_content_type="text/markdown",
    url="https://github.com/miintto/redis-lock-py",

    packages=find_packages(include=["redis_lock"]),

    python_requires=">=3.7",
    install_requires=get_requirements("requirements.txt"),

    keywords=[
        "redis", "distributed-lock", "python", "pubsub-messages", "asyncio"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    tests_require=["pytest", "pytest-asyncio"],
)
