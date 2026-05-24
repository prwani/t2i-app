"""Image generation page."""

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
    "Text generation",
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


def _uploaded_bytes(uploads) -> list[bytes]:
    return [upload.getvalue() for upload in uploads or []]


def _non_empty_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


st.title("Image Generate")

with st.sidebar:
    scenario = st.selectbox("Scenario", SCENARIOS)
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
prompt = st.text_area(prompt_label, height=120)

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

if scenario == "Brand template":
    colors_text = st.text_input("Brand colors", value="#0078D4, #FFFFFF")
    colors = [color.strip() for color in colors_text.split(",") if color.strip()]
    font_style = st.text_input("Font style", value="modern sans-serif")
    tone = st.text_input("Tone", value="professional")
    logo_description = st.text_input("Logo description", value="")
elif scenario == "Text rendering":
    text_to_render = st.text_input("Exact text to render")
elif scenario == "Aspect-ratio package":
    formats = st.multiselect(
        "Target formats",
        ["instagram_square", "instagram_story", "linkedin_banner", "desktop_hero", "mobile_story"],
        default=["instagram_square", "linkedin_banner"],
    )
elif scenario == "Multi-image composition":
    source_uploads = st.file_uploader(
        "Source images (2-16)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    upload_count = len(source_uploads or [])
    if upload_count and not 2 <= upload_count <= 16:
        st.warning("Multi-image composition requires 2 to 16 source images.")
elif scenario == "Inpainting":
    st.info("Optional mask must be a PNG with alpha transparency. Transparent areas are edited.")
    source_uploads = st.file_uploader("Source image", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=False)
    mask_upload = st.file_uploader("Optional alpha mask", type=["png"], accept_multiple_files=False)
elif scenario == "Product placement":
    source_uploads = st.file_uploader("Product image", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=False)
    environment_text = st.text_area(
        "Target environments (one per line)",
        value="on a premium retail shelf\non a kitchen counter",
        height=100,
    )
elif scenario == "Multi-turn refinement":
    refinement_text = st.text_area(
        "Refinement instructions (one per line)",
        value="Make the lighting more dramatic\nAdd a subtle reflection on the floor",
        height=120,
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
elif scenario == "Multi-image composition" and not 2 <= len(source_uploads or []) <= 16:
    disabled_reason = "Upload 2 to 16 source images."
elif scenario == "Inpainting" and source_uploads is None:
    disabled_reason = "Upload a source image."
elif scenario == "Product placement" and (source_uploads is None or not _non_empty_lines(environment_text)):
    disabled_reason = "Upload a product image and provide at least one environment."
elif scenario == "Multi-turn refinement" and not _non_empty_lines(refinement_text):
    disabled_reason = "Provide at least one refinement instruction."

if disabled_reason:
    st.caption(disabled_reason)

assets_key = f"generated_assets::{scenario}"
if st.button("Generate", type="primary", disabled=bool(disabled_reason)):
    with st.status("Generating images...", expanded=True) as status:
        try:
            if scenario == "Text generation":
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
                assets = run_async(
                    compose_uploaded_images(
                        _uploaded_bytes(source_uploads),
                        prompt,
                        size=size,
                        quality=quality,
                    )
                )
            elif scenario == "Inpainting":
                assets = run_async(
                    inpaint_uploaded_image(
                        source_uploads.getvalue(),
                        prompt,
                        mask=mask_upload.getvalue() if mask_upload else None,
                        size=size,
                        quality=quality,
                    )
                )
            elif scenario == "Product placement":
                assets = run_async(
                    place_product_assets(
                        source_uploads.getvalue(),
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
