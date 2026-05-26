"""Scenario metadata exposed to frontend clients."""
# ruff: noqa: E501

from __future__ import annotations

from typing import Literal, TypedDict


ScenarioId = Literal[
    "text-to-image",
    "brand-template",
    "text-rendering",
    "aspect-ratio-package",
    "multi-image-composition",
    "inpainting",
    "product-placement",
    "multi-turn-refinement",
]


class ExampleExtra(TypedDict, total=False):
    colors: str
    font_style: str
    tone: str
    logo_description: str
    text: str
    formats: list[str]
    environments: list[str]
    refinements: list[str]
    sample_images: list[str]
    sample_images_mask: str


class ScenarioMetadata(TypedDict):
    id: ScenarioId
    label: str
    service_label: str
    default_model: str
    forced_model: str | None
    example_prompts: list[str]
    example_extras: list[ExampleExtra]
    recommended_eval_layers: list[str]
    evaluation_recommended: bool
    compare_recommended: bool


SCENARIOS: dict[ScenarioId, ScenarioMetadata] = {
    "text-to-image": {
        "id": "text-to-image",
        "label": "Text-to-image generation",
        "service_label": "Text-to-image generation",
        "default_model": "MAI-Image-2e",
        "forced_model": None,
        "example_prompts": [
            "Photorealistic travel-style image for a tourism campaign: a friendly dog sitting in the foreground near the Gateway of India in Mumbai, looking toward the Arabian Sea. Show the full stone arch monument in the background, a lively crowd of visitors, warm late-afternoon light, natural shadows, realistic scale, and no readable text or watermark.",
            "Professional product-lifestyle photograph: a futuristic electric scooter parked outside a modern glass office at sunrise. Center the scooter as the hero subject, show subtle reflections on the pavement, warm golden light, clean urban architecture, premium mobility-brand mood, realistic materials, and no logos or readable text.",
            "Interior design editorial image: a cozy reading nook beside a window with a soft armchair, layered cushions, leafy plants, a wooden side table, an open book, and a cup of tea. Use warm ambient lighting, natural textures, calm neutral colors, inviting composition, and no people or readable text.",
            "Premium ecommerce hero image: a modern smartwatch on a dark reflective surface with blue accent lighting. Show crisp glass, brushed metal, subtle reflections, shallow depth of field, centered product framing with negative space for copy, photorealistic studio lighting, and no extra text or logos.",
            "Cinematic outdoor adventure scene: a mountain campsite under a clear starry sky with one softly glowing tent beside a small safe campfire. Use wide-angle composition, snow-capped peaks in the distance, cool moonlight balanced with warm tent light, atmospheric depth, realistic terrain, and no text.",
        ],
        "example_extras": [{}, {}, {}, {}, {}],
        "recommended_eval_layers": ["embedding", "rubric", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
    "brand-template": {
        "id": "brand-template",
        "label": "Brand template",
        "service_label": "Brand template",
        "default_model": "MAI-Image-2e",
        "forced_model": None,
        "example_prompts": [
            "Website launch banner for a secure cloud backup product aimed at small businesses. Show a clean abstract cloud vault, protected files, subtle shield motif, confident enterprise layout, room for headline copy on the left, polished SaaS visual style, and no readable text.",
            "Hero image for an AI productivity assistant that helps teams summarize meetings. Show a modern workspace with floating summary cards, calendar cues, and collaborative team silhouettes, friendly futuristic tone, soft gradients, clean UI-inspired composition, and no readable text.",
            "Square social media promotion for a premium fitness app limited-time discount. Show an energetic athlete silhouette, dynamic motion shapes, premium app-device mockup, bold high-contrast composition, space for offer text, and no readable text in the generated image.",
            "Website header for a sustainable home cleaning brand. Show fresh natural ingredients, reusable bottles, leafy accents, sunlight on a clean kitchen counter, calm editorial composition, eco-friendly premium mood, and no readable text.",
            "Product announcement visual for a developer observability dashboard. Show abstract monitoring graphs, signal traces, server health indicators, a dark technical interface style, precise futuristic lighting, space for announcement copy, and no readable text.",
        ],
        "example_extras": [
            {"colors": "#0078D4, #FFFFFF", "font_style": "modern sans-serif", "tone": "trustworthy", "logo_description": "blue shield icon"},
            {"colors": "#6B46C1, #F8FAFC", "font_style": "rounded modern", "tone": "helpful and efficient", "logo_description": "spark assistant mark"},
            {"colors": "#FF6B35, #111827", "font_style": "bold geometric", "tone": "energetic", "logo_description": "motion streak icon"},
            {"colors": "#2F855A, #FFF7ED", "font_style": "clean editorial", "tone": "natural and calm", "logo_description": "leaf wordmark"},
            {"colors": "#0F172A, #38BDF8", "font_style": "technical mono", "tone": "precise and confident", "logo_description": "signal graph mark"},
        ],
        "recommended_eval_layers": ["rubric", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
    "text-rendering": {
        "id": "text-rendering",
        "label": "Text rendering",
        "service_label": "Text rendering",
        "default_model": "MAI-Image-2e",
        "forced_model": None,
        "example_prompts": [
            "Minimal technology conference poster with a clean hierarchy: large bold headline at the top, medium subtitle centered below, and small location/date line near the bottom. Use abstract blue gradients, strong contrast, crisp sans-serif typography, generous margins, and ensure every quoted line is spelled exactly.",
            "Photorealistic coffee shop sidewalk chalkboard sign on a sunny street. Use large hand-lettered headline at the top, medium menu line in the middle, and small footer text at the bottom; high contrast cream lettering on dark board, warm cafe background blur, and exact spelling.",
            "Premium product label design on a matte black bottle in a studio setup. Use a large elegant brand name, a small uppercase tagline, and a tiny flavor note below; gold and off-white typography, centered vertical layout, crisp edges, and exact quoted text.",
            "Modern city billboard for a startup launch. Use oversized headline occupying most of the billboard, secondary call-to-action below, small date line in the corner, clean geometric typography, bright daylight urban setting, strong legibility from a distance, and exact quoted text.",
            "Children's book cover with playful illustrated style. Use a large whimsical title with curved baseline, smaller subtitle below, and a small author line at the bottom; cheerful color palette, friendly moonlit garden illustration, crisp readable lettering, and exact quoted text.",
        ],
        "example_extras": [
            {"text": "AI SUMMIT 2026\nBUILD THE FUTURE\nMumbai - July 12"},
            {"text": "FRESH BREW\nOAT LATTE + COLD FOAM\nToday Only"},
            {"text": "NOVA\nBOTANICAL TONIC\nCitrus Mint"},
            {"text": "LAUNCH DAY\nJOIN THE WAITLIST\nJune 30"},
            {"text": "THE MOON GARDEN\nA bedtime adventure\nBy Mira Sen"},
        ],
        "recommended_eval_layers": ["rubric", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
    "aspect-ratio-package": {
        "id": "aspect-ratio-package",
        "label": "Aspect-ratio package",
        "service_label": "Aspect-ratio package",
        "default_model": "gpt-image-2",
        "forced_model": None,
        "example_prompts": [
            "Polished SaaS product hero visual for a marketing campaign: floating analytics dashboards, soft blue-purple gradients, subtle glassmorphism, centered product narrative with safe negative space around edges for cropping across formats, no readable text.",
            "Luxury travel campaign image featuring a beach resort at golden hour: elegant infinity pool, palm silhouettes, warm sunlight, premium editorial photography, aspirational mood, central subject that works in square, portrait, and banner crops, no readable text.",
            "Modern hiring campaign visual for software engineers: diverse team collaboration around abstract code and cloud infrastructure shapes, optimistic lighting, professional tech-company aesthetic, strong central focal point with flexible crop-safe composition, no readable text.",
            "Product marketing image for noise-cancelling headphones: premium headphones floating above a soft acoustic wave pattern, dark-to-blue gradient, crisp reflections, centered hero product with negative space for layout variations, no logos or readable text.",
            "Clean educational course banner about cloud security: abstract shield, cloud nodes, secure network lines, calm blue and white palette, clear central visual metaphor, layout safe for social and desktop crops, no readable text.",
        ],
        "example_extras": [
            {"formats": ["instagram_square", "linkedin_banner", "desktop_hero"]},
            {"formats": ["instagram_square", "instagram_story", "mobile_story"]},
            {"formats": ["linkedin_banner", "desktop_hero"]},
            {"formats": ["instagram_square", "instagram_story"]},
            {"formats": ["linkedin_banner", "desktop_hero", "mobile_story"]},
        ],
        "recommended_eval_layers": ["embedding", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
    "multi-image-composition": {
        "id": "multi-image-composition",
        "label": "Multi-image composition",
        "service_label": "Multi-image composition",
        "default_model": "gpt-image-2",
        "forced_model": "gpt-image-2",
        "example_prompts": [
            "Create a realistic premium advertisement using Image 1 as the product photo and Image 2 as the background scene. Place the product naturally on the counter, match perspective and lighting, add realistic contact shadows and reflections, preserve the product shape and color, and do not add readable text.",
            "Use Image 1 as the main object and Image 2 as the destination scene. Place the object naturally into the scene at realistic scale, align camera angle, match ambient lighting, preserve object geometry and material, and keep the final image photorealistic with no extra text.",
            "Create a cohesive campaign visual using Image 1 as the product, Image 2 as the lighting reference, and Image 3 as the style reference. Preserve the product identity, apply the lighting mood and premium ad style, use a clean centered composition, and avoid readable text.",
            "Blend the uploaded references into a modern website hero image: use Image 1 as the UI reference, Image 2 as the hero background, and Image 3 as accent shapes. Compose a polished SaaS hero visual with balanced negative space, consistent colors, realistic depth, and no readable text.",
            "Compose a social media ad using Image 1 as the product, Image 2 as the background, and Image 3 as the style reference. Make the product the clear focal point, use dynamic modern lighting and shapes, preserve product details, and leave clean space for copy without generating text.",
        ],
        "example_extras": [
            {"sample_images": ["composition/example-1/background.png", "composition/example-1/product.png"]},
            {"sample_images": ["composition/example-2/object.png", "composition/example-2/scene.png"]},
            {"sample_images": ["composition/example-3/lighting-reference.png", "composition/example-3/product-reference.png", "composition/example-3/style-reference.png"]},
            {"sample_images": ["composition/example-4/accent-reference.png", "composition/example-4/hero-reference.png", "composition/example-4/ui-reference.png"]},
            {"sample_images": ["composition/example-5/background.png", "composition/example-5/product.png", "composition/example-5/style-reference.png"]},
        ],
        "recommended_eval_layers": ["rubric", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
    "inpainting": {
        "id": "inpainting",
        "label": "Inpainting",
        "service_label": "Inpainting",
        "default_model": "gpt-image-2",
        "forced_model": "gpt-image-2",
        "example_prompts": [
            "Change only the transparent masked region into a clean white studio background with soft natural shadows. Preserve all unmasked furniture, perspective, lighting direction, colors, and image edges exactly; do not add text or new objects.",
            "Change only the object inside the transparent mask to glossy emerald green ceramic while preserving its shape, size, highlights, shadows, camera angle, and surrounding white studio background. Do not modify unmasked areas or add text.",
            "Remove the unwanted object inside the transparent mask and fill the area naturally with the surrounding desk surface. Preserve the laptop, notebook, pen holder, lighting, perspective, and all unmasked objects exactly; no added text.",
            "Add a premium gift box only inside the transparent masked empty space. Match the tabletop perspective and studio lighting, add realistic contact shadow, keep all unmasked areas unchanged, and do not add any text or logo.",
            "Replace only the masked background area with a warm sunset beach scene while preserving the unmasked subject area, camera perspective, edge blending, and natural lighting. Do not alter unmasked details or add readable text.",
        ],
        "example_extras": [
            {"sample_images": ["inpainting/example-1/source.png"], "sample_images_mask": "inpainting/example-1/mask.png"},
            {"sample_images": ["inpainting/example-2/source.png"], "sample_images_mask": "inpainting/example-2/mask.png"},
            {"sample_images": ["inpainting/example-3/source.png"], "sample_images_mask": "inpainting/example-3/mask.png"},
            {"sample_images": ["inpainting/example-4/source.png"], "sample_images_mask": "inpainting/example-4/mask.png"},
            {"sample_images": ["inpainting/example-5/source.png"], "sample_images_mask": "inpainting/example-5/mask.png"},
        ],
        "recommended_eval_layers": ["rubric", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
    "product-placement": {
        "id": "product-placement",
        "label": "Product placement",
        "service_label": "Product placement",
        "default_model": "gpt-image-2",
        "forced_model": "gpt-image-2",
        "example_prompts": [
            "Use the uploaded product image as the exact hero product. Place it naturally into each environment with realistic scale, perspective, contact shadows, and reflections. Preserve product geometry, material, and color; do not invent labels or readable text.",
            "Create premium lifestyle product photography for each environment. Keep the uploaded product accurate and recognizable, adapt lighting to the scene, use shallow depth of field, realistic shadows, and a polished commercial photography style with no added text.",
            "Show the uploaded product as the clear hero object in each environment. Use centered composition, soft background blur, realistic surface contact, accurate material rendering, and preserve product shape and proportions without adding logos or text.",
            "Create ecommerce landing-page campaign images using the uploaded product. Place the product in clean aspirational environments, leave negative space for future copy, maintain product accuracy, match lighting and perspective, and generate no readable text.",
            "Preserve the uploaded product's shape, material, color, and any existing branding while adapting it to each environment. Use realistic shadows, scene-matched lighting, natural camera perspective, and avoid new labels, extra objects, or text.",
        ],
        "example_extras": [
            {"environments": ["on a marble kitchen counter", "inside a premium retail display", "on a sunny outdoor patio"], "sample_images": ["product-placement/example-1/product.png"]},
            {"environments": ["on a wooden desk near a window", "inside a modern living room", "on a hotel bedside table"], "sample_images": ["product-placement/example-2/product.png"]},
            {"environments": ["on a luxury store shelf", "in a minimalist studio setup", "inside a gift hamper"], "sample_images": ["product-placement/example-3/product.png"]},
            {"environments": ["on an ecommerce hero background", "in a lifestyle flat lay", "on a clean white product pedestal"], "sample_images": ["product-placement/example-4/product.png"]},
            {"environments": ["in a warm cafe scene", "on a travel packing table", "beside a laptop in a workspace"], "sample_images": ["product-placement/example-5/product.png"]},
        ],
        "recommended_eval_layers": ["rubric", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
    "multi-turn-refinement": {
        "id": "multi-turn-refinement",
        "label": "Multi-turn refinement",
        "service_label": "Multi-turn refinement",
        "default_model": "gpt-image-2",
        "forced_model": "gpt-image-2",
        "example_prompts": [
            "Premium product hero image of wireless earbuds on a dark reflective studio surface. Use centered composition, crisp highlights on glossy materials, subtle blue rim light, shallow depth of field, negative space for copy, and no readable text.",
            "Modern app launch visual with a smartphone mockup as the hero subject, abstract gradient background, floating UI cards, clean SaaS-style lighting, polished promotional composition, and no readable text.",
            "Cozy cafe interior with a laptop on a wooden table near a window, warm morning light, coffee cup, soft background blur, inviting productivity mood, realistic textures, and no readable text.",
            "Dramatic sports shoe advertisement on a dark wet studio floor. Show the shoe as the hero object with strong rim lighting, energetic motion accents, realistic reflections, premium athletic brand mood, and no readable text.",
            "Clean corporate banner showing teamwork and cloud technology through abstract people silhouettes, cloud nodes, secure connection lines, bright optimistic lighting, professional enterprise aesthetic, and no readable text.",
        ],
        "example_extras": [
            {"refinements": ["Make the lighting more dramatic", "Add a subtle reflection on the floor", "Make the background darker"]},
            {"refinements": ["Make the phone screen glow", "Add floating UI elements", "Increase contrast and polish"]},
            {"refinements": ["Add more plants", "Make the morning light warmer", "Add a notebook beside the laptop"]},
            {"refinements": ["Add motion blur accents", "Make the shoe color electric blue", "Add rain droplets on the floor"]},
            {"refinements": ["Add subtle cloud icons", "Make the people more diverse", "Use a brighter optimistic color palette"]},
        ],
        "recommended_eval_layers": ["rubric", "judge"],
        "evaluation_recommended": True,
        "compare_recommended": True,
    },
}


def get_scenario(scenario_id: str) -> ScenarioMetadata:
    try:
        return SCENARIOS[scenario_id]  # type: ignore[index]
    except KeyError as exc:
        raise ValueError(f"Unsupported scenario: {scenario_id}") from exc
