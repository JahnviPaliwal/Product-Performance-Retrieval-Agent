"""Unit tests for column vector retrieval using Sentence-Transformers and FAISS."""

import pytest
from analytics_agent.retrieval import ColumnRetriever, filter_profile_for_query, retrieve_relevant_columns


@pytest.fixture
def wide_profile():
    return {
        "num_rows": 1000,
        "num_columns": 12,
        "columns": [
            {"name": "customer_id", "dtype": "int64", "semantic_summary": "Unique customer identifier", "sample_values": ["101", "102"]},
            {"name": "first_name", "dtype": "object", "semantic_summary": "Customer first name", "sample_values": ["Alice", "Bob"]},
            {"name": "last_name", "dtype": "object", "semantic_summary": "Customer last name", "sample_values": ["Smith", "Jones"]},
            {"name": "annual_revenue", "dtype": "float64", "semantic_summary": "Annual purchase dollars revenue", "sample_values": ["15000", "24000"]},
            {"name": "product_discount", "dtype": "float64", "semantic_summary": "Promotional discount rate percent", "sample_values": ["0.10", "0.25"]},
            {"name": "credit_score", "dtype": "int64", "semantic_summary": "Credit rating score", "sample_values": ["720", "680"]},
            {"name": "country", "dtype": "object", "semantic_summary": "Billing country name", "sample_values": ["USA", "Canada"]},
            {"name": "device_type", "dtype": "object", "semantic_summary": "User device mobile or desktop", "sample_values": ["iOS", "Android"]},
            {"name": "order_timestamp", "dtype": "datetime64", "semantic_summary": "Order creation date and time", "sample_values": ["2026-01-01"]},
            {"name": "shipping_fee", "dtype": "float64", "semantic_summary": "Cost charged for delivery shipping", "sample_values": ["5.99", "12.50"]},
            {"name": "refund_issued", "dtype": "bool", "semantic_summary": "Whether refund was processed", "sample_values": ["True", "False"]},
            {"name": "loyalty_tier", "dtype": "object", "semantic_summary": "Customer reward membership tier", "sample_values": ["Gold", "Silver"]},
        ],
    }


def test_column_retriever_build_and_query(wide_profile):
    retriever = ColumnRetriever()
    retriever.build_index(wide_profile["columns"])

    results = retriever.retrieve("Which columns relate to sales, pricing, and revenue?", top_k=3)
    assert len(results) == 3
    retrieved_names = [col["name"] for col in results]
    assert any(name in retrieved_names for name in ["annual_revenue", "product_discount", "shipping_fee"])


def test_filter_profile_for_query_active(wide_profile):
    filtered = filter_profile_for_query(
        wide_profile,
        query="shipping and delivery logistics costs",
        top_k=4,
        enable_retrieval=True,
    )
    assert filtered["retrieval_applied"] is True
    assert len(filtered["columns"]) == 4
    names = [c["name"] for c in filtered["columns"]]
    assert "shipping_fee" in names


def test_filter_profile_retrieval_disabled(wide_profile):
    filtered = filter_profile_for_query(
        wide_profile,
        query="shipping fee",
        top_k=4,
        enable_retrieval=False,
    )
    assert filtered["retrieval_applied"] is False
    assert len(filtered["columns"]) == 12


def test_retrieve_relevant_columns_helper(wide_profile):
    col_names = retrieve_relevant_columns(
        wide_profile,
        query="customer profile identity name",
        top_k=3,
        enable_retrieval=True,
    )
    assert len(col_names) == 3
