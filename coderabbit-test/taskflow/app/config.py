import os


class Config:
    """Runtime configuration, overridable through the environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DB_PATH = os.environ.get("DB_PATH", "taskflow.db")
    TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))

    PAGE_SIZE_DEFAULT = 25
    PAGE_SIZE_MAX = 100

    MIN_PASSWORD_LENGTH = 12


class TestConfig(Config):
    SECRET_KEY = "test-key"
    TESTING = True
