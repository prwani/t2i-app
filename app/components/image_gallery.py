"""Image gallery component."""

import streamlit as st

from services import GeneratedAsset


def render_gallery(assets: list[GeneratedAsset], *, gallery_id: str = "gallery") -> None:
    """Render a focused preview with a thumbnail filmstrip."""

    if not assets:
        st.info("No images generated yet.")
        return

    index_key = f"{gallery_id}_selected_index"
    if index_key not in st.session_state:
        st.session_state[index_key] = 0
    st.session_state[index_key] = max(0, min(st.session_state[index_key], len(assets) - 1))

    if len(assets) > 1:
        st.caption("Select a thumbnail to preview it.")
        columns = st.columns(min(5, len(assets)))
        for index, asset in enumerate(assets):
            with columns[index % len(columns)]:
                selected = index == st.session_state[index_key]
                label = f"{'▶ ' if selected else ''}{index + 1}"
                if st.button(label, key=f"{gallery_id}-thumb-{index}", use_container_width=True):
                    st.session_state[index_key] = index
                    st.rerun()
                st.image(asset.result.image, use_container_width=True)

    selected_index = st.session_state[index_key]
    selected_asset = assets[selected_index]
    st.image(
        selected_asset.result.image,
        caption=selected_asset.caption or selected_asset.name,
        use_container_width=True,
    )
    st.download_button(
        "Download selected image",
        data=selected_asset.result.image,
        file_name=selected_asset.name,
        mime="image/png",
        key=f"download-selected-{gallery_id}-{selected_index}",
    )


def _asset_label(asset: GeneratedAsset, index: int) -> str:
    return f"{index + 1}. {asset.caption or asset.name}"
