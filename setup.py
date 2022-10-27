from setuptools import setup

setup(
    version="1.2.2",
    install_requires=[
        "pydantic",
        "shortuuid"
    ],
    extras_require={
        "dev": [
            "build",
            "black",
            "bandit",
            "coverage",
            "faker",
            "flake8",
            "freezegun",
            "isort",
            "mypy",
            "pytest",
            "twine",
            "yoyo-migrations",
        ],
    },
)
