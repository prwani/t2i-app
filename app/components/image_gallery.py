"""Image gallery component."""

import streamlit as st

from services import GeneratedAsset


def render_gallery(assets: list[GeneratedAsset]) -> None:
    if not assets:
        st.info("No images generated yet.")
        return
    columns = st.columns(min(3, len(assets)))
    for index, asset in enumerate(assets):
        with columns[index % len(columns)]:
            st.image(asset.result.image, caption=asset.name, use_container_width=True)
            st.download_button(
                "Download",
                data=asset.result.image,
                file_name=asset.name,
                mime="image/png",
                key=f"download-{asset.name}-{index}",
            )
