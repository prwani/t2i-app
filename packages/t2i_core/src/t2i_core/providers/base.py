"""Provider interfaces."""

from abc import ABC, abstractmethod

from t2i_core.types import EditResult, GenerationResult, VideoResult


class ImageProvider(ABC):
    """Abstract base for image generation models."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1,
    ) -> list[GenerationResult]:
        """Generate one or more images."""


class EditableImageProvider(ImageProvider):
    """Extended interface for models that support image editing."""

    @abstractmethod
    async def edit(
        self,
        images: list[bytes],
        prompt: str,
        mask: bytes | None = None,
        **kwargs: object,
    ) -> list[EditResult]:
        """Edit one or more source images."""


class VideoProvider(ABC):
    """Abstract base for async video generation providers."""

    @abstractmethod
    async def create_video(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        seconds: int = 8,
        **kwargs: object,
    ) -> str:
        """Create a video job and return its job ID."""

    @abstractmethod
    async def poll_video(self, job_id: str) -> VideoResult:
        """Poll a video job."""

    @abstractmethod
    async def download_video(self, generation_id: str) -> bytes:
        """Download generated video bytes."""
