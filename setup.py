from setuptools import setup

setup(
    version="1.0.1-5",
    install_requires=[
        "pydantic",
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
