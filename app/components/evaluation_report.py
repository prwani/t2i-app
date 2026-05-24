"""Evaluation report rendering."""

import streamlit as st

from t2i_core.types import EvaluationReport


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
