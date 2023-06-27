def sample_settings() -> dict:
    return dict(
        firebase_project_id="firebase_project_id",
        firebase_service_account_id="firebase_service_account_id",
        firebase_web_api_key="firebase_web_api_key",
        shopify_client_id="shopify_client_id",
        shopify_client_secret="shopify_client_secret",
        shopify_private_app_admin_api_access_token="shopify_private_app_admin_api_access_token",
        twillio_service_id="twillio_service_id",
        twillio_acount_id="twillio_acount_id",
        twillio_auth_token="twillio_auth_token",
        sendgrid_api_key="sendgrid_api_key",
        bucket_name="bucket_name",
        open_ai_secret_key="open_ai_secret_key",
        ship24_api_key="ship24_api_key",
    )


def sample_env() -> dict:
    return dict(
        JWT_SECRET_KEY="JWT_SECRET_KEY",
        JWT_ALGORITHM="JWT_ALGORITHM",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES="60",
        JWT_REFRESH_TOKEN_EXPIRE_MINUTES="1440",
        JWT_AUDIENCE="JWT_AUDIENCE",
        SENTRY_DSN="",
        SENTRY_TRACES_SAMPLE_RATE="1.0",
        SUPPORT_EMAIL="a@a.com",
        SECRET_MANAGER_PROJECT_ID="SECRET_MANAGER_PROJECT_ID",
        SECRET_MANAGER_SECRET_ID="SECRET_MANAGER_SECRET_ID",
        SECRET_MANAGER_VERSION_ID="latest",
    )
