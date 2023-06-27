from functools import lru_cache

from fastapi import Depends

from app.external.secret_manager import SecretManager
from app.secrets import Secrets


@lru_cache
def init_setting(secret_manager: SecretManager = Depends(SecretManager)):
    j = secret_manager.get_secrets()
    return Secrets(**j)
