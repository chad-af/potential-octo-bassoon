import os

import fireo
import openai
from app.service_container import ServiceContainer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    healthcheck,
    shopify,
)
from app.external.secret_manager import SecretManager

container = ServiceContainer()
secrets = SecretManager().get_secrets()
container.config.from_dict(secrets)
openai.api_key = container.config.open_ai_secret_key

app = FastAPI()
app.container = container

origins = [
    "http://localhost",
    "http://localhost:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(healthcheck.router)
app.include_router(auth.router)
app.include_router(shopify.router)

fireo.connection(from_file=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
