import os

from dotenv import load_dotenv

environment = os.getenv("ENV_VAR")

if environment == "prod":
    load_dotenv("prod.env")
elif environment == "staging":
    load_dotenv("staging.env")
else:
    load_dotenv("local.env")


class EnvironmentVariables:
    SUPPORT_EMAIL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int
    JWT_AUDIENCE: str
    SENTRY_DSN: str
    SECRET_MANAGER_PROJECT_ID: str
    SECRET_MANAGER_SECRET_ID: str
    SECRET_MANAGER_VERSION_ID: str

    def __init__(self):
        self.SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL")
        self.JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
            os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
        )
        self.JWT_REFRESH_TOKEN_EXPIRE_MINUTES = int(
            os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_MINUTES")
        )
        self.JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE")
        self.SENTRY_DSN = os.environ.get("SENTRY_DSN")

        self.SECRET_MANAGER_PROJECT_ID = os.environ.get("SECRET_MANAGER_PROJECT_ID")
        self.SECRET_MANAGER_SECRET_ID = os.environ.get("SECRET_MANAGER_SECRET_ID")
        self.SECRET_MANAGER_VERSION_ID = os.environ.get("SECRET_MANAGER_VERSION_ID")


env = EnvironmentVariables()
