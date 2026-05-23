import pytest
from pydantic import ValidationError

from t2i_core.clients import get_openai_client, get_vision_token_provider
from t2i_core.settings import Settings


class FakeCredential:
    def get_token(self, scope: str):
        self.scope = scope

        class Token:
            token = "fake-token"

        return Token()


def test_settings_normalizes_urls(settings: Settings) -> None:
    assert settings.openai_base_url == "https://example-openai.openai.azure.com/openai/v1/"
    assert settings.vision_endpoint == "https://example-vision.cognitiveservices.azure.com"


def test_settings_requires_endpoints() -> None:
    with pytest.raises(ValidationError):
        Settings()


def test_scope_must_end_with_default() -> None:
    with pytest.raises(ValidationError, match="must end with '/.default'"):
        Settings(
            AZURE_OPENAI_ENDPOINT="https://example-openai.openai.azure.com/",
            AZURE_VISION_ENDPOINT="https://example-vision.cognitiveservices.azure.com/",
            AZURE_OPENAI_SCOPE="https://ai.azure.com",
        )


def test_vision_token_provider_uses_configured_scope(settings: Settings) -> None:
    credential = FakeCredential()
    provider = get_vision_token_provider(settings, credential)  # type: ignore[arg-type]

    assert provider() == "fake-token"
    assert credential.scope == "https://cognitiveservices.azure.com/.default"


def test_openai_client_uses_normalized_base_url(settings: Settings) -> None:
    client = get_openai_client(settings, credential=FakeCredential())  # type: ignore[arg-type]

    assert str(client.base_url) == "https://example-openai.openai.azure.com/openai/v1/"
