from setuptools import setup

setup(
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
