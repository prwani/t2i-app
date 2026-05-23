"""Multi-turn image refinement scenario."""

from pydantic import BaseModel, Field

from t2i_core.providers.base import EditableImageProvider
from t2i_core.types import EditResult, GenerationResult


class RefinementChain(BaseModel):
    """Images and prompts produced during iterative refinement."""

    initial: GenerationResult
    refinements: list[EditResult] = Field(default_factory=list)


async def refine_image_chain(
    provider: EditableImageProvider,
    initial_prompt: str,
    refinement_instructions: list[str],
    *,
    size: str = "1024x1024",
    quality: str = "high",
) -> RefinementChain:
    """Generate an initial image, then apply each refinement instruction."""

    initial = (await provider.generate(initial_prompt, size=size, quality=quality, n=1))[0]
    current_image = initial.image
    results: list[EditResult] = []
    for instruction in refinement_instructions:
        result = (await provider.edit([current_image], instruction, size=size, quality=quality, n=1))[0]
        results.append(result)
        current_image = result.image
    return RefinementChain(initial=initial, refinements=results)
