"""Evaluation report rendering."""

import streamlit as st

from t2i_core.types import EvaluationReport


def render_evaluation_summary(reports: list[EvaluationReport]) -> None:
    """Render the 3 x N evaluation-technique score matrix."""

    if not reports:
        return
    st.subheader("Score summary")
    st.caption("Rows are evaluation approaches; columns are images.")
    st.dataframe(score_matrix(reports), use_container_width=True)


def score_matrix(reports: list[EvaluationReport]) -> list[dict[str, str]]:
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


def render_evaluation_report(report: EvaluationReport) -> None:
    metrics = st.columns(4)
    metrics[0].metric("Composite", f"{report.composite_score:.3f}")
    metrics[1].metric("Decision", report.threshold_decision)
    metrics[2].metric(
        "Embedding",
        f"{report.embedding.cosine_similarity:.3f}" if report.embedding else "Skipped",
    )
    metrics[3].metric(
        "Judge",
        f"{report.llm_judge.average_score:.2f}" if report.llm_judge else "Skipped",
    )

    if report.rubric:
        st.subheader("Prompt rubric")
        st.write(f"Score: {report.rubric.rubric_score:.3f}")
        st.dataframe(
            [
                {
                    "category": item.category,
                    "description": item.description,
                    "answer": item.answer,
                    "confidence": item.confidence,
                    "reasoning": item.reasoning,
                }
                for item in report.rubric.attributes
            ],
            use_container_width=True,
        )

    if report.llm_judge:
        st.subheader("Judge")
        st.json(report.llm_judge.model_dump(mode="json"))

    st.subheader("Threshold reasons")
    for reason in report.threshold_reasons:
        st.write(f"- {reason}")
