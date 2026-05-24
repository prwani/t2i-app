"""Image gallery component."""

import hashlib

import streamlit as st

from services import GeneratedAsset


def render_gallery(assets: list[GeneratedAsset], *, gallery_id: str = "gallery") -> None:
    """Render a navigable gallery with large preview and previous/next controls."""

    if not assets:
        st.info("No images generated yet.")
        return

    index_key = f"{gallery_id}_selected_index"
    if index_key not in st.session_state:
        st.session_state[index_key] = 0
    st.session_state[index_key] = max(0, min(st.session_state[index_key], len(assets) - 1))

    if len(assets) > 1:
        previous_column, select_column, next_column = st.columns([1, 4, 1])
        with previous_column:
            if st.button("Previous", key=f"{gallery_id}-previous", disabled=st.session_state[index_key] == 0):
                st.session_state[index_key] -= 1
                st.rerun()
        with select_column:
            labels = [_asset_label(asset, index) for index, asset in enumerate(assets)]
            selected_label = st.selectbox(
                "Image",
                labels,
                index=st.session_state[index_key],
                key=f"{gallery_id}-select",
            )
            st.session_state[index_key] = labels.index(selected_label)
        with next_column:
            if st.button(
                "Next",
                key=f"{gallery_id}-next",
                disabled=st.session_state[index_key] >= len(assets) - 1,
            ):
                st.session_state[index_key] += 1
                st.rerun()

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
        key=f"download-selected-{gallery_id}-{selected_index}-{_image_hash(selected_asset)}",
    )

    st.subheader("Thumbnails")
    columns = st.columns(min(4, len(assets)))
    for index, asset in enumerate(assets):
        with columns[index % len(columns)]:
            st.image(asset.result.image, caption=_asset_label(asset, index), use_container_width=True)
            if st.button("Select", key=f"{gallery_id}-thumb-{index}"):
                st.session_state[index_key] = index
                st.rerun()


def _asset_label(asset: GeneratedAsset, index: int) -> str:
    return f"{index + 1}. {asset.caption or asset.name}"


def _image_hash(asset: GeneratedAsset) -> str:
    return hashlib.sha256(asset.result.image).hexdigest()[:12]
