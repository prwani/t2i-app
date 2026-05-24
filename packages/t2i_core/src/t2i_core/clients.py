"""Azure client construction helpers."""

import os
from collections.abc import Callable

from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import httpx
from openai import AsyncOpenAI

from t2i_core.settings import Settings


def get_openai_token_provider(
    settings: Settings,
    credential: DefaultAzureCredential | None = None,
) -> Callable[[], str]:
    """Return a token provider that refreshes Azure OpenAI tokens as needed."""

    return get_bearer_token_provider(
        credential or _default_credential(),
        settings.azure_openai_scope,
    )


def get_openai_client(
    settings: Settings,
    credential: DefaultAzureCredential | None = None,
) -> AsyncOpenAI:
    """Build an OpenAI v1 client for Azure OpenAI using Azure AD token refresh."""

    token_provider = get_openai_token_provider(settings, credential)

    async def provide_token() -> str:
        return token_provider()

    return AsyncOpenAI(
        base_url=settings.openai_base_url,
        api_key=provide_token,
    )


def get_vision_token_provider(
    settings: Settings,
    credential: DefaultAzureCredential | None = None,
) -> Callable[[], str]:
    """Return a token provider for Azure AI Vision requests."""

    token_credential = credential or _default_credential()

    def provide_token() -> str:
        token: AccessToken = token_credential.get_token(settings.azure_vision_scope)
        return token.token

    return provide_token


def get_http_client(**kwargs: object) -> httpx.AsyncClient:
    """Create an async HTTP client for REST endpoints not covered by the SDK."""

    return httpx.AsyncClient(**kwargs)


def _default_credential() -> DefaultAzureCredential:
    managed_identity_client_id = os.getenv("AZURE_CLIENT_ID")
    if managed_identity_client_id:
        return DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
    return DefaultAzureCredential()
