"""Compare uploaded images."""

import streamlit as st

from components.evaluation_report import render_evaluation_report
from services import evaluate_image, run_async
from t2i_core.types import EvaluationReport


def _score_matrix(reports: list[EvaluationReport]) -> list[dict[str, str]]:
    rows = [
        {"Evaluation approach": "Embedding"},
        {"Evaluation approach": "Rubric"},
        {"Evaluation approach": "Judge"},
    ]
    for index, report in enumerate(reports, start=1):
        image_name = report.image_path or f"Image {index}"
        rows[0][image_name] = (
            f"{report.embedding.cosine_similarity:.3f}" if report.embedding else "Skipped"
        )
        rows[1][image_name] = f"{report.rubric.rubric_score:.3f}" if report.rubric else "Skipped"
        rows[2][image_name] = (
            f"{report.llm_judge.average_score:.2f}/5" if report.llm_judge else "Skipped"
        )
    return rows


st.title("Compare")

uploads = st.file_uploader(
    "Images to compare",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)
prompt = st.text_area("Shared prompt", height=120)
layers = st.multiselect("Layers", ["embedding", "rubric", "judge"], default=["embedding", "rubric", "judge"])

if st.button("Evaluate comparison", type="primary", disabled=not uploads or not prompt.strip() or not layers):
    reports = []
    with st.status("Evaluating images...", expanded=True):
        for upload in uploads:
            st.write(f"Evaluating {upload.name}")
            try:
                reports.append(
                    run_async(
                        evaluate_image(
                            upload.getvalue(),
                            prompt,
                            layers,  # type: ignore[arg-type]
                            image_path=upload.name,
                        )
                    )
                )
            except Exception as exc:
                st.error(f"Evaluation failed for {upload.name}: {exc}")
    st.session_state["compare_reports"] = reports

reports = st.session_state.get("compare_reports", [])
if reports:
    st.subheader("Score summary")
    st.caption("Rows are evaluation approaches; columns are uploaded images.")
    st.dataframe(_score_matrix(reports), use_container_width=True)

for report in reports:
    st.subheader(report.image_path or "Image")
    render_evaluation_report(report)
