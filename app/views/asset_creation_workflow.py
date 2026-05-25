"""Asset creation workflow page."""

from pathlib import Path

import streamlit as st

from components.evaluation_report import render_evaluation_report, render_evaluation_summary
from components.image_gallery import render_gallery
from services import (
    compose_uploaded_images,
    evaluate_generated_assets,
    generate_aspect_package,
    generate_brand_template_assets,
    generate_images,
    generate_text_rendering_assets,
    improve_prompt_with_ai,
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
        "Example prompt 1": "Photorealistic travel-style image for a tourism campaign: a friendly dog sitting in the foreground near the Gateway of India in Mumbai, looking toward the Arabian Sea. Show the full stone arch monument in the background, a lively crowd of visitors, warm late-afternoon light, natural shadows, realistic scale, and no readable text or watermark.",
        "Example prompt 2": "Professional product-lifestyle photograph: a futuristic electric scooter parked outside a modern glass office at sunrise. Center the scooter as the hero subject, show subtle reflections on the pavement, warm golden light, clean urban architecture, premium mobility-brand mood, realistic materials, and no logos or readable text.",
        "Example prompt 3": "Interior design editorial image: a cozy reading nook beside a window with a soft armchair, layered cushions, leafy plants, a wooden side table, an open book, and a cup of tea. Use warm ambient lighting, natural textures, calm neutral colors, inviting composition, and no people or readable text.",
        "Example prompt 4": "Premium ecommerce hero image: a modern smartwatch on a dark reflective surface with blue accent lighting. Show crisp glass, brushed metal, subtle reflections, shallow depth of field, centered product framing with negative space for copy, photorealistic studio lighting, and no extra text or logos.",
        "Example prompt 5": "Cinematic outdoor adventure scene: a mountain campsite under a clear starry sky with one softly glowing tent beside a small safe campfire. Use wide-angle composition, snow-capped peaks in the distance, cool moonlight balanced with warm tent light, atmospheric depth, realistic terrain, and no text.",
    },
    "Brand template": {
        "Example prompt 1": "Website launch banner for a secure cloud backup product aimed at small businesses. Show a clean abstract cloud vault, protected files, subtle shield motif, confident enterprise layout, room for headline copy on the left, polished SaaS visual style, and no readable text.",
        "Example prompt 2": "Hero image for an AI productivity assistant that helps teams summarize meetings. Show a modern workspace with floating summary cards, calendar cues, and collaborative team silhouettes, friendly futuristic tone, soft gradients, clean UI-inspired composition, and no readable text.",
        "Example prompt 3": "Square social media promotion for a premium fitness app limited-time discount. Show an energetic athlete silhouette, dynamic motion shapes, premium app-device mockup, bold high-contrast composition, space for offer text, and no readable text in the generated image.",
        "Example prompt 4": "Website header for a sustainable home cleaning brand. Show fresh natural ingredients, reusable bottles, leafy accents, sunlight on a clean kitchen counter, calm editorial composition, eco-friendly premium mood, and no readable text.",
        "Example prompt 5": "Product announcement visual for a developer observability dashboard. Show abstract monitoring graphs, signal traces, server health indicators, a dark technical interface style, precise futuristic lighting, space for announcement copy, and no readable text.",
    },
    "Text rendering": {
        "Example prompt 1": "Minimal technology conference poster with a clean hierarchy: large bold headline at the top, medium subtitle centered below, and small location/date line near the bottom. Use abstract blue gradients, strong contrast, crisp sans-serif typography, generous margins, and ensure every quoted line is spelled exactly.",
        "Example prompt 2": "Photorealistic coffee shop sidewalk chalkboard sign on a sunny street. Use large hand-lettered headline at the top, medium menu line in the middle, and small footer text at the bottom; high contrast cream lettering on dark board, warm cafe background blur, and exact spelling.",
        "Example prompt 3": "Premium product label design on a matte black bottle in a studio setup. Use a large elegant brand name, a small uppercase tagline, and a tiny flavor note below; gold and off-white typography, centered vertical layout, crisp edges, and exact quoted text.",
        "Example prompt 4": "Modern city billboard for a startup launch. Use oversized headline occupying most of the billboard, secondary call-to-action below, small date line in the corner, clean geometric typography, bright daylight urban setting, strong legibility from a distance, and exact quoted text.",
        "Example prompt 5": "Children's book cover with playful illustrated style. Use a large whimsical title with curved baseline, smaller subtitle below, and a small author line at the bottom; cheerful color palette, friendly moonlit garden illustration, crisp readable lettering, and exact quoted text.",
    },
    "Aspect-ratio package": {
        "Example prompt 1": "Polished SaaS product hero visual for a marketing campaign: floating analytics dashboards, soft blue-purple gradients, subtle glassmorphism, centered product narrative with safe negative space around edges for cropping across formats, no readable text.",
        "Example prompt 2": "Luxury travel campaign image featuring a beach resort at golden hour: elegant infinity pool, palm silhouettes, warm sunlight, premium editorial photography, aspirational mood, central subject that works in square, portrait, and banner crops, no readable text.",
        "Example prompt 3": "Modern hiring campaign visual for software engineers: diverse team collaboration around abstract code and cloud infrastructure shapes, optimistic lighting, professional tech-company aesthetic, strong central focal point with flexible crop-safe composition, no readable text.",
        "Example prompt 4": "Product marketing image for noise-cancelling headphones: premium headphones floating above a soft acoustic wave pattern, dark-to-blue gradient, crisp reflections, centered hero product with negative space for layout variations, no logos or readable text.",
        "Example prompt 5": "Clean educational course banner about cloud security: abstract shield, cloud nodes, secure network lines, calm blue and white palette, clear central visual metaphor, layout safe for social and desktop crops, no readable text.",
    },
    "Multi-image composition": {
        "Example prompt 1": "Create a realistic premium advertisement using Image 1 as the product photo and Image 2 as the background scene. Place the product naturally on the counter, match perspective and lighting, add realistic contact shadows and reflections, preserve the product shape and color, and do not add readable text.",
        "Example prompt 2": "Use Image 1 as the main object and Image 2 as the destination scene. Place the object naturally into the scene at realistic scale, align camera angle, match ambient lighting, preserve object geometry and material, and keep the final image photorealistic with no extra text.",
        "Example prompt 3": "Create a cohesive campaign visual using Image 1 as the product, Image 2 as the lighting reference, and Image 3 as the style reference. Preserve the product identity, apply the lighting mood and premium ad style, use a clean centered composition, and avoid readable text.",
        "Example prompt 4": "Blend the uploaded references into a modern website hero image: use Image 1 as the UI reference, Image 2 as the hero background, and Image 3 as accent shapes. Compose a polished SaaS hero visual with balanced negative space, consistent colors, realistic depth, and no readable text.",
        "Example prompt 5": "Compose a social media ad using Image 1 as the product, Image 2 as the background, and Image 3 as the style reference. Make the product the clear focal point, use dynamic modern lighting and shapes, preserve product details, and leave clean space for copy without generating text.",
    },
    "Inpainting": {
        "Example prompt 1": "Change only the transparent masked region into a clean white studio background with soft natural shadows. Preserve all unmasked furniture, perspective, lighting direction, colors, and image edges exactly; do not add text or new objects.",
        "Example prompt 2": "Change only the object inside the transparent mask to glossy emerald green ceramic while preserving its shape, size, highlights, shadows, camera angle, and surrounding white studio background. Do not modify unmasked areas or add text.",
        "Example prompt 3": "Remove the unwanted object inside the transparent mask and fill the area naturally with the surrounding desk surface. Preserve the laptop, notebook, pen holder, lighting, perspective, and all unmasked objects exactly; no added text.",
        "Example prompt 4": "Add a premium gift box only inside the transparent masked empty space. Match the tabletop perspective and studio lighting, add realistic contact shadow, keep all unmasked areas unchanged, and do not add any text or logo.",
        "Example prompt 5": "Replace only the masked background area with a warm sunset beach scene while preserving the unmasked subject area, camera perspective, edge blending, and natural lighting. Do not alter unmasked details or add readable text.",
    },
    "Product placement": {
        "Example prompt 1": "Use the uploaded product image as the exact hero product. Place it naturally into each environment with realistic scale, perspective, contact shadows, and reflections. Preserve product geometry, material, and color; do not invent labels or readable text.",
        "Example prompt 2": "Create premium lifestyle product photography for each environment. Keep the uploaded product accurate and recognizable, adapt lighting to the scene, use shallow depth of field, realistic shadows, and a polished commercial photography style with no added text.",
        "Example prompt 3": "Show the uploaded product as the clear hero object in each environment. Use centered composition, soft background blur, realistic surface contact, accurate material rendering, and preserve product shape and proportions without adding logos or text.",
        "Example prompt 4": "Create ecommerce landing-page campaign images using the uploaded product. Place the product in clean aspirational environments, leave negative space for future copy, maintain product accuracy, match lighting and perspective, and generate no readable text.",
        "Example prompt 5": "Preserve the uploaded product's shape, material, color, and any existing branding while adapting it to each environment. Use realistic shadows, scene-matched lighting, natural camera perspective, and avoid new labels, extra objects, or text.",
    },
    "Multi-turn refinement": {
        "Example prompt 1": "Premium product hero image of wireless earbuds on a dark reflective studio surface. Use centered composition, crisp highlights on glossy materials, subtle blue rim light, shallow depth of field, negative space for copy, and no readable text.",
        "Example prompt 2": "Modern app launch visual with a smartphone mockup as the hero subject, abstract gradient background, floating UI cards, clean SaaS-style lighting, polished promotional composition, and no readable text.",
        "Example prompt 3": "Cozy cafe interior with a laptop on a wooden table near a window, warm morning light, coffee cup, soft background blur, inviting productivity mood, realistic textures, and no readable text.",
        "Example prompt 4": "Dramatic sports shoe advertisement on a dark wet studio floor. Show the shoe as the hero object with strong rim lighting, energetic motion accents, realistic reflections, premium athletic brand mood, and no readable text.",
        "Example prompt 5": "Clean corporate banner showing teamwork and cloud technology through abstract people silhouettes, cloud nodes, secure connection lines, bright optimistic lighting, professional enterprise aesthetic, and no readable text.",
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


def _default_eval_layers(selected_scenario: str) -> list[str]:
    if selected_scenario in {"Brand template", "Text rendering"}:
        return ["rubric", "judge"]
    if selected_scenario in {
        "Multi-image composition",
        "Inpainting",
        "Product placement",
        "Multi-turn refinement",
    }:
        return ["rubric", "judge"]
    if selected_scenario == "Aspect-ratio package":
        return ["embedding", "judge"]
    return ["embedding", "rubric", "judge"]


def _best_asset_message(assets) -> str | None:
    evaluated = [asset for asset in assets if asset.evaluation is not None]
    if not evaluated:
        return None
    best = max(evaluated, key=lambda asset: asset.evaluation.composite_score)
    return (
        f"Best candidate: {best.name} "
        f"(composite {best.evaluation.composite_score:.3f}, decision {best.evaluation.threshold_decision})"
    )


def _render_workflow_stepper(step: str, has_assets: bool, has_evaluation: bool) -> None:
    st.markdown(
        """
        <style>
        .workflow-stepper {display:flex; gap:.75rem; align-items:center; margin:.5rem 0 1rem 0;}
        .workflow-step {flex:1; border-radius:999px; padding:.75rem 1rem; font-weight:700; text-align:center; border:1px solid rgba(148,163,184,.45);}
        .workflow-step.done {background:rgba(34,197,94,.16); color:rgb(21,128,61); border-color:rgba(34,197,94,.55);}
        .workflow-step.active {background:rgba(59,130,246,.18); color:rgb(29,78,216); border-color:rgba(59,130,246,.55);}
        .workflow-step.locked {background:rgba(148,163,184,.10); color:rgb(100,116,139);}
        .workflow-connector {width:44px; height:2px; background:rgba(148,163,184,.45);}
        </style>
        """,
        unsafe_allow_html=True,
    )
    generate_class = "done" if has_assets else "active"
    evaluate_class = "done" if has_evaluation else "active" if step == "evaluate" and has_assets else "locked"
    st.markdown(
        f"""
        <div class="workflow-stepper">
          <div class="workflow-step {generate_class}">{"✅ " if has_assets else ""}1. Generate</div>
          <div class="workflow-connector"></div>
          <div class="workflow-step {evaluate_class}">{"✅ " if has_evaluation else ""}2. Evaluate / Compare</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _comparison_cards(assets) -> None:
    evaluated = [asset for asset in assets if asset.evaluation is not None]
    if not evaluated:
        return
    best = max(evaluated, key=lambda asset: asset.evaluation.composite_score)
    columns = st.columns(min(4, len(evaluated)))
    for index, asset in enumerate(evaluated):
        report = asset.evaluation
        with columns[index % len(columns)]:
            st.image(asset.result.image, use_container_width=True)
            st.markdown(f"**{'🏆 ' if asset is best else ''}{asset.name}**")
            st.metric("Composite", f"{report.composite_score:.3f}")
            st.caption(f"Decision: {report.threshold_decision}")


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
        index=0 if model_disabled else 2,
        disabled=model_disabled,
        help="MAI-Image-2e is the default for generation-only scenarios. Editing scenarios require GPT-Image-2.",
    )
    if model_disabled:
        model = "gpt-image-2"
        st.info("This scenario requires GPT-Image-2.")
    quality = st.selectbox("Quality", ["low", "medium", "high"], index=2)
    size = st.selectbox("Size", ["1024x1024", "1536x1024", "1024x1536"])
    count = st.slider("Images", 1, 4, 1, disabled=scenario in GPT_ONLY_SCENARIOS)

assets_key = f"generated_assets::{scenario}"
eval_layers_key = f"eval_layers::{scenario}"
assets = st.session_state.get(assets_key, [])
has_evaluation = any(asset.evaluation is not None for asset in assets)
step_key = f"workflow_step::{scenario}"
if step_key not in st.session_state:
    st.session_state[step_key] = "evaluate" if assets else "generate"
if not assets:
    st.session_state[step_key] = "generate"

st.title("Asset Creation Workflow")
_render_workflow_stepper(st.session_state[step_key], bool(assets), has_evaluation)

nav_columns = st.columns([1, 1, 5])
with nav_columns[0]:
    if st.button("Generate", key=f"go-generate::{scenario}", use_container_width=True):
        st.session_state[step_key] = "generate"
        st.rerun()
with nav_columns[1]:
    if st.button(
        "Evaluate / Compare",
        key=f"go-evaluate::{scenario}",
        disabled=not assets,
        use_container_width=True,
    ):
        st.session_state[step_key] = "evaluate"
        st.rerun()

show_generate = st.session_state[step_key] == "generate"
show_evaluate = st.session_state[step_key] == "evaluate" and bool(assets)
if show_generate:
    st.subheader("Generate")

prompt_label = "Prompt"
if scenario == "Brand template":
    prompt_label = "Content brief"
elif scenario == "Text rendering":
    prompt_label = "Visual context"
elif scenario == "Product placement":
    prompt_label = "Optional placement guidance"
prompt_key = f"prompt::{scenario}::{selected_example}"
if prompt_key not in st.session_state:
    st.session_state[prompt_key] = _example_value(scenario, selected_example)

prompt_column, improve_column = st.columns([4, 1])
with improve_column:
    st.write("")
    if st.button(
        "✨ Improve with AI",
        disabled=not st.session_state.get(prompt_key, "").strip(),
        help="Use the configured text LLM to rewrite this prompt using image-generation prompting best practices.",
    ):
        with st.spinner("Improving prompt..."):
            try:
                st.session_state[prompt_key] = run_async(
                    improve_prompt_with_ai(st.session_state[prompt_key], scenario)
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Prompt improvement failed: {exc}")
with prompt_column:
    prompt = st.text_area(
        prompt_label,
        height=120,
        key=prompt_key,
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

if st.button("Generate asset", type="primary", disabled=bool(disabled_reason)):
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
            st.session_state[step_key] = "evaluate"
            status.update(label="Generation complete.", state="complete")
            st.rerun()
        except Exception as exc:
            status.update(label="Generation failed.", state="error")
            st.error(f"Generation failed: {exc}")
assets = st.session_state.get(assets_key, [])
if show_evaluate:
    st.divider()
    st.subheader("Evaluate / Compare")
    st.caption("Use this immediately after generation to compare outputs and pick the best candidate.")
    eval_columns = st.columns([3, 1, 1])
    with eval_columns[0]:
        eval_layers = st.multiselect(
            "Evaluation layers",
            ["embedding", "rubric", "judge"],
            default=_default_eval_layers(scenario),
            key=eval_layers_key,
        )
    with eval_columns[1]:
        sort_by_score = st.checkbox("Sort by score", value=len(assets) > 1)
    with eval_columns[2]:
        st.write("")
        evaluate_clicked = st.button(
            "Evaluate results",
            disabled=not eval_layers,
            key=f"evaluate::{scenario}",
            type="secondary",
        )

    if evaluate_clicked:
        with st.status("Evaluating generated results...", expanded=True) as status:
            try:
                evaluated_assets = run_async(
                    evaluate_generated_assets(
                        assets,
                        eval_layers,  # type: ignore[arg-type]
                    )
                )
                st.session_state[assets_key] = evaluated_assets
                st.session_state[f"{assets_key}_selected_index"] = 0
                assets = evaluated_assets
                status.update(label="Evaluation complete.", state="complete")
            except Exception as exc:
                status.update(label="Evaluation failed.", state="error")
                st.error(f"Evaluation failed: {exc}")

    reports = [asset.evaluation for asset in assets if asset.evaluation is not None]
    display_assets = (
        sorted(
            assets,
            key=lambda asset: asset.evaluation.composite_score if asset.evaluation is not None else -1,
            reverse=True,
        )
        if reports and sort_by_score
        else assets
    )
    if reports:
        render_evaluation_summary([asset.evaluation for asset in display_assets if asset.evaluation is not None])
        best_message = _best_asset_message(assets)
        if best_message:
            st.success(best_message)
        _comparison_cards(display_assets)

    render_gallery(display_assets, gallery_id=assets_key)

    reports = [asset.evaluation for asset in assets if asset.evaluation is not None]
    if reports:
        st.subheader("Detailed evaluation results")
        for asset in assets:
            if asset.evaluation is not None:
                with st.expander(asset.name):
                    render_evaluation_report(asset.evaluation)
elif assets:
    st.divider()
    st.subheader("Generated preview")
    render_gallery(assets, gallery_id=assets_key)
    if st.button("Continue to Evaluate / Compare", type="primary"):
        st.session_state[step_key] = "evaluate"
        st.rerun()
