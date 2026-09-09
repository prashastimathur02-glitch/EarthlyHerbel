import os


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "fallback-development-key"
    )

    DATABASE_HOST = os.getenv(
        "DATABASE_HOST",
        "localhost"
    )

    DATABASE_PORT = os.getenv(
        "DATABASE_PORT",
        "5432"
    )

    DATABASE_NAME = os.getenv(
        "DATABASE_NAME",
        "earthlyherbel"
    )

    DATABASE_USER = os.getenv(
        "DATABASE_USER",
        "postgres"
    )

    DATABASE_PASSWORD = os.getenv(
        "DATABASE_PASSWORD"
    )