"""Streamlit home page for the T2I app."""

import streamlit as st


st.set_page_config(page_title="T2I App", page_icon="T2I", layout="wide")

st.title("T2I Image Generation and Evaluation")
st.write(
    "Generate, evaluate, compare, and rank image assets with Azure Foundry models. "
    "Video generation is deferred until video model access is available."
)

st.info(
    "Production auth is handled by Microsoft Entra ID at Azure Container Apps ingress. "
    "The app uses Azure AD or managed identity for Foundry and Vision API calls."
)

st.subheader("Pages")
st.write("- Image Generate: create images with GPT-Image-2, MAI-Image-2, or MAI-Image-2e.")
st.write("- Evaluate: score an uploaded image with selected evaluation layers.")
st.write("- Compare: evaluate multiple images against the same prompt.")
st.write("- Batch Rank: generate GPT-Image-2 variations and rank them.")

st.subheader("Deployment")
st.write(
    "For Azure Container Apps deployment, see `docs/azure-container-apps.md`. "
    "Use a managed identity with Cognitive Services roles on the Azure AI resources."
)
