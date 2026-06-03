"""Runtime settings loaded from environment variables."""

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from t2i_core.evaluation.config import EvalModelConfig, EvaluationThresholds


DEFAULT_EVAL_WEIGHTS = {
    "embedding_score": 0.20,
    "rubric_score": 0.45,
    "llm_judge_score": 0.35,
}


class Settings(BaseSettings):
    """Configuration for providers, evaluators, and Azure auth."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    foundry_project_endpoint: HttpUrl | None = Field(default=None, alias="FOUNDRY_PROJECT_ENDPOINT")
    azure_openai_endpoint: HttpUrl = Field(alias="AZURE_OPENAI_ENDPOINT")
    azure_vision_endpoint: HttpUrl = Field(alias="AZURE_VISION_ENDPOINT")
    azure_openai_timeout_seconds: float = Field(
        default=300.0,
        alias="AZURE_OPENAI_TIMEOUT_SECONDS",
        gt=0,
    )

    azure_openai_scope: str = Field(
        default="https://ai.azure.com/.default",
        alias="AZURE_OPENAI_SCOPE",
    )
    azure_vision_scope: str = Field(
        default="https://cognitiveservices.azure.com/.default",
        alias="AZURE_VISION_SCOPE",
    )

    mai_image_deployment: str = Field(default="MAI-Image-2", alias="MAI_IMAGE_2_DEPLOYMENT")
    mai_image_efficient_deployment: str = Field(
        default="MAI-Image-2e",
        alias="MAI_IMAGE_2E_DEPLOYMENT",
    )
    mai_image_25_flash_deployment: str = Field(
        default="MAI-Image-2.5-Flash",
        alias="MAI_IMAGE_2_5_FLASH_DEPLOYMENT",
    )
    mai_image_25_deployment: str = Field(
        default="MAI-Image-2.5",
        alias="MAI_IMAGE_2_5_DEPLOYMENT",
    )
    gpt_image_deployment: str = Field(default="gpt-image-2", alias="GPT_IMAGE_2_DEPLOYMENT")
    sora_deployment: str = Field(default="sora-2", alias="SORA_2_DEPLOYMENT")

    eval_decomposer_deployment: str = Field(default="o4-mini", alias="EVAL_DECOMPOSER_DEPLOYMENT")
    eval_rubric_deployment: str = Field(default="o4-mini", alias="EVAL_RUBRIC_DEPLOYMENT")
    eval_judge_deployment: str = Field(default="gpt-5.4", alias="EVAL_JUDGE_DEPLOYMENT")
    eval_unified_deployment: str | None = Field(default=None, alias="EVAL_UNIFIED_DEPLOYMENT")

    eval_thresholds: EvaluationThresholds = Field(default_factory=EvaluationThresholds)
    eval_weights: dict[str, float] = Field(default_factory=lambda: DEFAULT_EVAL_WEIGHTS.copy())

    @field_validator("azure_openai_scope", "azure_vision_scope")
    @classmethod
    def scopes_must_be_default_scopes(cls, value: str) -> str:
        if not value.endswith("/.default"):
            raise ValueError("Azure token scopes must end with '/.default'")
        return value

    @property
    def openai_base_url(self) -> str:
        """Azure OpenAI v1 base URL with exactly one slash before /openai/v1/."""

        return f"{str(self.azure_openai_endpoint).rstrip('/')}/openai/v1/"

    @property
    def foundry_services_endpoint(self) -> str:
        """Azure AI Foundry services endpoint used by MAI APIs."""

        if self.foundry_project_endpoint is not None:
            project_endpoint = str(self.foundry_project_endpoint).rstrip("/")
            return project_endpoint.split("/api/projects/", 1)[0]
        openai_endpoint = str(self.azure_openai_endpoint).rstrip("/")
        return openai_endpoint.replace(".openai.azure.com", ".services.ai.azure.com")

    @property
    def vision_endpoint(self) -> str:
        """Normalized Azure AI Vision endpoint."""

        return str(self.azure_vision_endpoint).rstrip("/")

    @property
    def eval_model_config(self) -> EvalModelConfig:
        if self.eval_unified_deployment:
            return EvalModelConfig(
                decomposer_deployment=self.eval_unified_deployment,
                rubric_deployment=self.eval_unified_deployment,
                judge_deployment=self.eval_unified_deployment,
                decomposer_is_o_series=False,
                rubric_is_o_series=False,
                judge_is_o_series=False,
            )
        return EvalModelConfig(
            decomposer_deployment=self.eval_decomposer_deployment,
            rubric_deployment=self.eval_rubric_deployment,
            judge_deployment=self.eval_judge_deployment,
            decomposer_is_o_series=self.eval_decomposer_deployment.startswith("o"),
            rubric_is_o_series=self.eval_rubric_deployment.startswith("o"),
            judge_is_o_series=self.eval_judge_deployment.startswith("o"),
        )
