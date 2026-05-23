"""Azure client construction helpers."""

from collections.abc import Callable

import httpx
from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncOpenAI

from t2i_core.settings import Settings


def get_openai_token_provider(
    settings: Settings,
    credential: DefaultAzureCredential | None = None,
) -> Callable[[], str]:
    """Return a token provider that refreshes Azure OpenAI tokens as needed."""

    return get_bearer_token_provider(
        credential or DefaultAzureCredential(),
        settings.azure_openai_scope,
    )


def get_openai_client(
    settings: Settings,
    credential: DefaultAzureCredential | None = None,
) -> AsyncOpenAI:
    """Build an AsyncOpenAI client for Azure OpenAI v1 endpoints."""

    return AsyncOpenAI(
        base_url=settings.openai_base_url,
        api_key=get_openai_token_provider(settings, credential),
    )


def get_vision_token_provider(
    settings: Settings,
    credential: DefaultAzureCredential | None = None,
) -> Callable[[], str]:
    """Return a token provider for Azure AI Vision requests."""

    token_credential = credential or DefaultAzureCredential()

    def provide_token() -> str:
        token: AccessToken = token_credential.get_token(settings.azure_vision_scope)
        return token.token

    return provide_token


def get_http_client(**kwargs: object) -> httpx.AsyncClient:
    """Create an async HTTP client for REST endpoints not covered by the SDK."""

    return httpx.AsyncClient(**kwargs)
