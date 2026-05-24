"""Image generation page."""

from pathlib import Path

import streamlit as st

from components.image_gallery import render_gallery
from services import (
    compose_uploaded_images,
    generate_aspect_package,
    generate_brand_template_assets,
    generate_images,
    generate_text_rendering_assets,
    inpaint_uploaded_image,
    place_product_assets,
    refine_image_assets,
    run_async,
)


SCENARIOS = [
    "Text-to-image generation",
    "Brand template",
    "Text rendering",
    "Aspect-ratio package",
    "Multi-image composition",
    "Inpainting",
    "Product placement",
    "Multi-turn refinement",
]
GPT_ONLY_SCENARIOS = {
    "Multi-image composition",
    "Inpainting",
    "Product placement",
    "Multi-turn refinement",
}
EXAMPLE_PROMPTS = {
    "Text-to-image generation": {
        "Example prompt 1": "A dog sitting at Gateway of India and enjoying the sea view with many people in the background.",
        "Example prompt 2": "A futuristic electric scooter parked outside a modern glass office at sunrise.",
        "Example prompt 3": "A cozy reading nook with warm lighting, plants, and a cup of tea on a wooden table.",
        "Example prompt 4": "A premium smartwatch product photo on a dark reflective surface with blue accent lighting.",
        "Example prompt 5": "A cinematic mountain campsite under a starry sky with a glowing tent.",
    },
    "Brand template": {
        "Example prompt 1": "Launch banner for a secure cloud backup product aimed at small businesses.",
        "Example prompt 2": "Hero image for an AI productivity assistant that helps teams summarize meetings.",
        "Example prompt 3": "Social post announcing a limited-time discount for a premium fitness app.",
        "Example prompt 4": "Website header for a sustainable home cleaning brand.",
        "Example prompt 5": "Product announcement visual for a developer observability dashboard.",
    },
    "Text rendering": {
        "Example prompt 1": "Minimal conference poster with multi-line typography, bold headline, smaller subtitle, and abstract blue gradients.",
        "Example prompt 2": "Coffee shop sidewalk sign with large hand-lettered headline, medium menu line, and small footer text on a sunny street.",
        "Example prompt 3": "Premium product label on a matte black bottle with large brand name, small tagline, and tiny flavor note.",
        "Example prompt 4": "Startup launch billboard with oversized headline, secondary call-to-action, and small date line in a modern city scene.",
        "Example prompt 5": "Children's book cover with playful title lettering, curved subtitle, and small author line.",
    },
    "Aspect-ratio package": {
        "Example prompt 1": "A polished SaaS product hero visual with floating dashboards and soft gradients.",
        "Example prompt 2": "A luxury travel campaign image featuring a beach resort at golden hour.",
        "Example prompt 3": "A modern hiring campaign visual for software engineers.",
        "Example prompt 4": "A product marketing image for noise-cancelling headphones.",
        "Example prompt 5": "A clean educational course banner about cloud security.",
    },
    "Multi-image composition": {
        "Example prompt 1": "Combine the product photo with the background image into a realistic premium advertisement.",
        "Example prompt 2": "Place the main object from the first image naturally into the scene from the second image.",
        "Example prompt 3": "Create a cohesive campaign visual using all uploaded references with matching lighting.",
        "Example prompt 4": "Blend the uploaded elements into a modern website hero image.",
        "Example prompt 5": "Compose a social media ad using the product, background, and style reference images.",
    },
    "Inpainting": {
        "Example prompt 1": "Replace the selected area with a clean white studio background.",
        "Example prompt 2": "Change the object in the selected area to glossy emerald green.",
        "Example prompt 3": "Remove the unwanted object and fill the area naturally.",
        "Example prompt 4": "Add a premium gift box in the selected empty space.",
        "Example prompt 5": "Turn the selected background into a warm sunset beach scene.",
    },
    "Product placement": {
        "Example prompt 1": "Keep the product accurate and make it look naturally photographed in each environment.",
        "Example prompt 2": "Create premium lifestyle product photography with realistic shadows and reflections.",
        "Example prompt 3": "Show the product as the hero object with shallow depth of field.",
        "Example prompt 4": "Make the product suitable for an ecommerce landing page campaign.",
        "Example prompt 5": "Preserve product shape and branding while adapting lighting to each scene.",
    },
    "Multi-turn refinement": {
        "Example prompt 1": "A premium product hero image of wireless earbuds on a reflective surface.",
        "Example prompt 2": "A modern app launch visual with a smartphone mockup and abstract gradient background.",
        "Example prompt 3": "A cozy cafe interior with a laptop on the table and morning light.",
        "Example prompt 4": "A dramatic sports shoe advertisement on a dark studio floor.",
        "Example prompt 5": "A clean corporate banner showing teamwork and cloud technology.",
    },
}
EXAMPLE_EXTRAS = {
    "Brand template": {
        "Example prompt 1": {"colors": "#0078D4, #FFFFFF", "font_style": "modern sans-serif", "tone": "trustworthy", "logo_description": "blue shield icon"},
        "Example prompt 2": {"colors": "#6B46C1, #F8FAFC", "font_style": "rounded modern", "tone": "helpful and efficient", "logo_description": "spark assistant mark"},
        "Example prompt 3": {"colors": "#FF6B35, #111827", "font_style": "bold geometric", "tone": "energetic", "logo_description": "motion streak icon"},
        "Example prompt 4": {"colors": "#2F855A, #FFF7ED", "font_style": "clean editorial", "tone": "natural and calm", "logo_description": "leaf wordmark"},
        "Example prompt 5": {"colors": "#0F172A, #38BDF8", "font_style": "technical mono", "tone": "precise and confident", "logo_description": "signal graph mark"},
    },
    "Text rendering": {
        "Example prompt 1": {"text": "AI SUMMIT 2026\nBUILD THE FUTURE\nMumbai - July 12"},
        "Example prompt 2": {"text": "FRESH BREW\nOAT LATTE + COLD FOAM\nToday Only"},
        "Example prompt 3": {"text": "NOVA\nBOTANICAL TONIC\nCitrus Mint"},
        "Example prompt 4": {"text": "LAUNCH DAY\nJOIN THE WAITLIST\nJune 30"},
        "Example prompt 5": {"text": "THE MOON GARDEN\nA bedtime adventure\nBy Mira Sen"},
    },
    "Aspect-ratio package": {
        "Example prompt 1": {"formats": ["instagram_square", "linkedin_banner", "desktop_hero"]},
        "Example prompt 2": {"formats": ["instagram_square", "instagram_story", "mobile_story"]},
        "Example prompt 3": {"formats": ["linkedin_banner", "desktop_hero"]},
        "Example prompt 4": {"formats": ["instagram_square", "instagram_story"]},
        "Example prompt 5": {"formats": ["linkedin_banner", "desktop_hero", "mobile_story"]},
    },
    "Product placement": {
        "Example prompt 1": {"environments": "on a marble kitchen counter\ninside a premium retail display\non a sunny outdoor patio"},
        "Example prompt 2": {"environments": "on a wooden desk near a window\ninside a modern living room\non a hotel bedside table"},
        "Example prompt 3": {"environments": "on a luxury store shelf\nin a minimalist studio setup\ninside a gift hamper"},
        "Example prompt 4": {"environments": "on an ecommerce hero background\nin a lifestyle flat lay\non a clean white product pedestal"},
        "Example prompt 5": {"environments": "in a warm cafe scene\non a travel packing table\nbeside a laptop in a workspace"},
    },
    "Multi-turn refinement": {
        "Example prompt 1": {"refinements": "Make the lighting more dramatic\nAdd a subtle reflection on the floor\nMake the background darker"},
        "Example prompt 2": {"refinements": "Make the phone screen glow\nAdd floating UI elements\nIncrease contrast and polish"},
        "Example prompt 3": {"refinements": "Add more plants\nMake the morning light warmer\nAdd a notebook beside the laptop"},
        "Example prompt 4": {"refinements": "Add motion blur accents\nMake the shoe color electric blue\nAdd rain droplets on the floor"},
        "Example prompt 5": {"refinements": "Add subtle cloud icons\nMake the people more diverse\nUse a brighter optimistic color palette"},
    },
}


def _uploaded_bytes(uploads) -> list[bytes]:
    return [upload.getvalue() for upload in uploads or []]


def _non_empty_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _example_value(scenario: str, selected_example: str) -> str:
    if selected_example == "Custom":
        return ""
    return EXAMPLE_PROMPTS[scenario][selected_example]


def _example_extra(scenario: str, selected_example: str, key: str, default):
    if selected_example == "Custom":
        return default
    return EXAMPLE_EXTRAS.get(scenario, {}).get(selected_example, {}).get(key, default)


def _sample_composition_images(selected_example: str) -> list[tuple[str, bytes]]:
    """Load GPT-generated local PNG sample inputs for composition examples."""

    sample_dir = _sample_asset_dir("composition", selected_example)
    return [(path.name, path.read_bytes()) for path in sorted(sample_dir.glob("*.png"))]


def _sample_inpainting_assets(selected_example: str) -> tuple[bytes, bytes]:
    sample_dir = _sample_asset_dir("inpainting", selected_example)
    return (sample_dir / "source.png").read_bytes(), (sample_dir / "mask.png").read_bytes()


def _sample_product_image(selected_example: str) -> bytes:
    return (_sample_asset_dir("product-placement", selected_example) / "product.png").read_bytes()


def _sample_asset_dir(scenario_slug: str, selected_example: str) -> Path:
    label = selected_example if selected_example != "Custom" else "Example prompt 1"
    sample_dirs = {
        "Example prompt 1": "example-1",
        "Example prompt 2": "example-2",
        "Example prompt 3": "example-3",
        "Example prompt 4": "example-4",
        "Example prompt 5": "example-5",
    }
    return Path(__file__).resolve().parents[1] / "sample_assets" / scenario_slug / sample_dirs[label]


st.title("Image Generate")

with st.sidebar:
    scenario = st.selectbox("Scenario", SCENARIOS)
    selected_example = st.selectbox(
        "Example prompt",
        ["Custom", *EXAMPLE_PROMPTS[scenario].keys()],
        help="Choose an example to prefill the scenario inputs.",
    )
    model_disabled = scenario in GPT_ONLY_SCENARIOS
    model = st.selectbox(
        "Model",
        ["gpt-image-2", "MAI-Image-2", "MAI-Image-2e"],
        disabled=model_disabled,
        help="Editing scenarios require GPT-Image-2.",
    )
    if model_disabled:
        model = "gpt-image-2"
        st.info("This scenario requires GPT-Image-2.")
    quality = st.selectbox("Quality", ["low", "medium", "high"], index=2)
    size = st.selectbox("Size", ["1024x1024", "1536x1024", "1024x1536"])
    count = st.slider("Images", 1, 4, 1, disabled=scenario in GPT_ONLY_SCENARIOS)

prompt_label = "Prompt"
if scenario == "Brand template":
    prompt_label = "Content brief"
elif scenario == "Text rendering":
    prompt_label = "Visual context"
elif scenario == "Product placement":
    prompt_label = "Optional placement guidance"
prompt = st.text_area(
    prompt_label,
    value=_example_value(scenario, selected_example),
    height=120,
    key=f"prompt::{scenario}::{selected_example}",
)

colors: list[str] = []
font_style = ""
tone = ""
logo_description = ""
text_to_render = ""
formats: list[str] = []
source_uploads = []
mask_upload = None
environment_text = ""
refinement_text = ""
composition_input_count = 0
use_sample_inpainting = False
use_sample_product = False
sample_inpainting_source: bytes | None = None
sample_inpainting_mask: bytes | None = None
sample_product_image: bytes | None = None

if scenario == "Brand template":
    colors_text = st.text_input(
        "Brand colors",
        value=_example_extra(scenario, selected_example, "colors", "#0078D4, #FFFFFF"),
        key=f"colors::{selected_example}",
    )
    colors = [color.strip() for color in colors_text.split(",") if color.strip()]
    font_style = st.text_input(
        "Font style",
        value=_example_extra(scenario, selected_example, "font_style", "modern sans-serif"),
        key=f"font_style::{selected_example}",
    )
    tone = st.text_input(
        "Tone",
        value=_example_extra(scenario, selected_example, "tone", "professional"),
        key=f"tone::{selected_example}",
    )
    logo_description = st.text_input(
        "Logo description",
        value=_example_extra(scenario, selected_example, "logo_description", ""),
        key=f"logo::{selected_example}",
    )
elif scenario == "Text rendering":
    text_to_render = st.text_area(
        "Exact text to render",
        value=_example_extra(scenario, selected_example, "text", ""),
        height=100,
        key=f"text::{selected_example}",
    )
elif scenario == "Aspect-ratio package":
    formats = st.multiselect(
        "Target formats",
        ["instagram_square", "instagram_story", "linkedin_banner", "desktop_hero", "mobile_story"],
        default=_example_extra(
            scenario,
            selected_example,
            "formats",
            ["instagram_square", "linkedin_banner"],
        ),
        key=f"formats::{selected_example}",
    )
elif scenario == "Multi-image composition":
    sample_inputs = _sample_composition_images(selected_example)
    use_sample_inputs = st.checkbox(
        "Use sample input images for this example",
        value=selected_example != "Custom",
        disabled=selected_example == "Custom",
    )
    if use_sample_inputs:
        st.caption("Sample inputs")
        sample_columns = st.columns(len(sample_inputs))
        for column, (name, image_bytes) in zip(sample_columns, sample_inputs, strict=True):
            with column:
                st.image(image_bytes, use_container_width=True)
                st.caption(name)
    source_uploads = st.file_uploader(
        "Or upload source images (2-16)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    composition_input_count = len(sample_inputs) if use_sample_inputs else len(source_uploads or [])
    if composition_input_count and not 2 <= composition_input_count <= 16:
        st.warning("Multi-image composition requires 2 to 16 source images.")
elif scenario == "Inpainting":
    st.info("Optional mask must be a PNG with alpha transparency. Transparent areas are edited.")
    use_sample_inpainting = st.checkbox(
        "Use sample source image and mask for this example",
        value=selected_example != "Custom",
        disabled=selected_example == "Custom",
    )
    if use_sample_inpainting:
        sample_inpainting_source, sample_inpainting_mask = _sample_inpainting_assets(selected_example)
        source_column, mask_column = st.columns(2)
        with source_column:
            st.image(sample_inpainting_source, use_container_width=True)
            st.caption("sample source.png")
        with mask_column:
            st.image(sample_inpainting_mask, use_container_width=True)
            st.caption("sample mask.png")
    source_uploads = st.file_uploader("Source image", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=False)
    mask_upload = st.file_uploader("Optional alpha mask", type=["png"], accept_multiple_files=False)
elif scenario == "Product placement":
    use_sample_product = st.checkbox(
        "Use sample product image for this example",
        value=selected_example != "Custom",
        disabled=selected_example == "Custom",
    )
    if use_sample_product:
        sample_product_image = _sample_product_image(selected_example)
        st.image(sample_product_image, width=280)
        st.caption("sample product.png")
    source_uploads = st.file_uploader("Product image", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=False)
    environment_text = st.text_area(
        "Target environments (one per line)",
        value=_example_extra(
            scenario,
            selected_example,
            "environments",
            "on a premium retail shelf\non a kitchen counter",
        ),
        height=100,
        key=f"environments::{selected_example}",
    )
elif scenario == "Multi-turn refinement":
    refinement_text = st.text_area(
        "Refinement instructions (one per line)",
        value=_example_extra(
            scenario,
            selected_example,
            "refinements",
            "Make the lighting more dramatic\nAdd a subtle reflection on the floor",
        ),
        height=120,
        key=f"refinements::{selected_example}",
    )

disabled_reason = ""
if not prompt.strip():
    disabled_reason = "Enter a prompt or brief."
elif scenario == "Brand template" and (not colors or not font_style.strip() or not tone.strip()):
    disabled_reason = "Provide brand colors, font style, and tone."
elif scenario == "Text rendering" and not text_to_render.strip():
    disabled_reason = "Provide exact text to render."
elif scenario == "Aspect-ratio package" and not formats:
    disabled_reason = "Select at least one target format."
elif scenario == "Multi-image composition" and not 2 <= composition_input_count <= 16:
    disabled_reason = "Upload 2 to 16 source images."
elif scenario == "Inpainting" and source_uploads is None and not use_sample_inpainting:
    disabled_reason = "Upload a source image."
elif scenario == "Product placement" and (
    (source_uploads is None and not use_sample_product) or not _non_empty_lines(environment_text)
):
    disabled_reason = "Upload a product image and provide at least one environment."
elif scenario == "Multi-turn refinement" and not _non_empty_lines(refinement_text):
    disabled_reason = "Provide at least one refinement instruction."

if disabled_reason:
    st.caption(disabled_reason)

assets_key = f"generated_assets::{scenario}"
if st.button("Generate", type="primary", disabled=bool(disabled_reason)):
    with st.status("Generating images...", expanded=True) as status:
        try:
            if scenario == "Text-to-image generation":
                assets = run_async(generate_images(prompt, model, size=size, quality=quality, n=count))
            elif scenario == "Brand template":
                assets = run_async(
                    generate_brand_template_assets(
                        prompt,
                        model,
                        colors=colors,
                        font_style=font_style,
                        tone=tone,
                        logo_description=logo_description or None,
                        size=size,
                        quality=quality,
                        n=count,
                    )
                )
            elif scenario == "Text rendering":
                assets = run_async(
                    generate_text_rendering_assets(
                        prompt,
                        model,
                        text=text_to_render,
                        size=size,
                        quality=quality,
                        n=count,
                    )
                )
            elif scenario == "Aspect-ratio package":
                assets = run_async(generate_aspect_package(prompt, model, formats, quality=quality))
            elif scenario == "Multi-image composition":
                composition_images = (
                    [image_bytes for _, image_bytes in sample_inputs]
                    if use_sample_inputs
                    else _uploaded_bytes(source_uploads)
                )
                assets = run_async(
                    compose_uploaded_images(
                        composition_images,
                        prompt,
                        size=size,
                        quality=quality,
                    )
                )
            elif scenario == "Inpainting":
                source_image = sample_inpainting_source if use_sample_inpainting else source_uploads.getvalue()
                mask_image = (
                    sample_inpainting_mask
                    if use_sample_inpainting
                    else mask_upload.getvalue() if mask_upload else None
                )
                assets = run_async(
                    inpaint_uploaded_image(
                        source_image,
                        prompt,
                        mask=mask_image,
                        size=size,
                        quality=quality,
                    )
                )
            elif scenario == "Product placement":
                product_image = sample_product_image if use_sample_product else source_uploads.getvalue()
                assets = run_async(
                    place_product_assets(
                        product_image,
                        _non_empty_lines(environment_text),
                        size=size,
                        quality=quality,
                    )
                )
            else:
                assets = run_async(
                    refine_image_assets(
                        prompt,
                        _non_empty_lines(refinement_text),
                        size=size,
                        quality=quality,
                    )
                )
            st.session_state[assets_key] = assets
            st.session_state[f"{assets_key}_selected_index"] = 0
            status.update(label="Generation complete.", state="complete")
        except Exception as exc:
            status.update(label="Generation failed.", state="error")
            st.error(f"Generation failed: {exc}")

render_gallery(st.session_state.get(assets_key, []), gallery_id=assets_key)
