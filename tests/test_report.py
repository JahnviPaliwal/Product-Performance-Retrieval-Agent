"""Unit tests for ReportLab PDF report generation."""

import pandas as pd
from analytics_agent.quality import compute_quality_report
from analytics_agent.report import generate_pdf_report


def test_generate_pdf_report():
    df = pd.DataFrame({
        "sales": [100.0, 250.0, 300.0, 450.0],
        "category": ["A", "B", "A", "C"],
        "discount": [0.0, 0.1, 0.05, 0.2],
    })
    quality_report = compute_quality_report(df)
    insights = [
        {"title": "Sales Distribution", "insight_type": "distribution", "description": "Spread of sales"},
        {"title": "Top Categories", "insight_type": "categorical_patterns", "description": "Frequencies"},
    ]
    executed_results = {
        "distribution": df[["sales", "discount"]].describe(),
        "categorical_patterns": {"category": {"A": 2, "B": 1, "C": 1}},
    }
    qa_history = [
        {"question": "What is the max sale?", "answer": "The maximum sales figure is 450.0."}
    ]

    pdf_bytes = generate_pdf_report(
        dataset_name="test_dataset.csv",
        df=df,
        quality_report=quality_report,
        insights=insights,
        executed_results=executed_results,
        qa_history=qa_history,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic header bytes
    assert pdf_bytes.startswith(b"%PDF-")
