from pydantic import BaseSettings, BaseConfig, Extra


class Secrets(BaseSettings):
    firebase_project_id: str
    firebase_service_account_id: str
    firebase_web_api_key: str
    shopify_client_id: str
    shopify_client_secret: str
    shopify_private_app_admin_api_access_token: str
    twillio_service_id: str
    twillio_acount_id: str
    twillio_auth_token: str
    sendgrid_api_key: str
    bucket_name: str
    open_ai_secret_key: str
    ship24_api_key: str

    class Config(BaseConfig):
        env_prefix: str = ""
        validate_all: bool = True
        extra: Extra = Extra.ignore
        arbitrary_types_allowed: bool = True
        case_sensitive: bool = False
