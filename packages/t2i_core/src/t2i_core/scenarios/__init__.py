"""Image generation scenario helpers."""

from t2i_core.scenarios.aspect_ratio_adaptation import adapt_aspect_ratios
from t2i_core.scenarios.batch_variations import generate_ranked_variations
from t2i_core.scenarios.brand_template import BrandTemplate, generate_brand_asset
from t2i_core.scenarios.inpainting import inpaint_image
from t2i_core.scenarios.multi_image_composition import compose_images
from t2i_core.scenarios.multi_turn_refinement import refine_image_chain
from t2i_core.scenarios.product_placement import place_product
from t2i_core.scenarios.text_rendering import generate_text_rendering

__all__ = [
    "BrandTemplate",
    "adapt_aspect_ratios",
    "compose_images",
    "generate_brand_asset",
    "generate_ranked_variations",
    "generate_text_rendering",
    "inpaint_image",
    "place_product",
    "refine_image_chain",
]
