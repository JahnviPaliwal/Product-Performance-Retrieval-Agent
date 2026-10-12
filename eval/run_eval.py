"""Evaluation harness for testing router accuracy and failure modes across sample datasets.

Usage:
    python eval/run_eval.py
"""

import json
import os
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List

# Ensure src is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from analytics_agent.router import WHITELISTED_INSIGHTS, classify_intent_route


def run_evaluation() -> Dict[str, Any]:
    """Execute evaluation over all test cases in eval/test_cases.json and record metrics."""
    base_dir = os.path.dirname(__file__)
    cases_path = os.path.join(base_dir, "test_cases.json")
    results_dir = os.path.abspath(os.path.join(base_dir, "..", "results"))
    os.makedirs(results_dir, exist_ok=True)

    with open(cases_path, "r", encoding="utf-8") as f:
        test_cases: List[Dict[str, Any]] = json.load(f)

    detailed_results = []
    correct_count = 0
    failure_types = defaultdict(int)
    latencies = []

    # Confusion matrix counters: TP, FP, FN per class
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    for case in test_cases:
        cid = case["id"]
        dataset = case["dataset"]
        question = case["question"]
        expected = case["expected_route"]
        needs_review = case.get("needs_human_review", False)

        t_start = time.perf_counter()
        failure_reason = None
        predicted = None

        try:
            predicted = classify_intent_route(question)
            latency_ms = (time.perf_counter() - t_start) * 1000.0

            if predicted not in WHITELISTED_INSIGHTS:
                failure_reason = "unknown_insight"
                failure_types["unknown_insight"] += 1
            elif predicted == expected:
                correct_count += 1
                tp[expected] += 1
            else:
                failure_reason = f"mismatched_route (expected {expected}, got {predicted})"
                failure_types["mismatched_route"] += 1
                fp[predicted] += 1
                fn[expected] += 1

        except Exception as e:
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            failure_reason = f"exception ({type(e).__name__}: {e})"
            failure_types["exception"] += 1
            fn[expected] += 1

        latencies.append(latency_ms)
        detailed_results.append({
            "id": cid,
            "dataset": dataset,
            "question": question,
            "expected_route": expected,
            "predicted_route": predicted,
            "correct": failure_reason is None,
            "failure_reason": failure_reason,
            "latency_ms": round(latency_ms, 2),
            "needs_human_review": needs_review,
        })

    total = len(test_cases)
    accuracy = round((correct_count / total), 4) if total > 0 else 0.0
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    # Per-category precision, recall, f1
    per_insight = {}
    for itype in sorted(WHITELISTED_INSIGHTS):
        c_tp = tp[itype]
        c_fp = fp[itype]
        c_fn = fn[itype]
        precision = round(c_tp / (c_tp + c_fp), 4) if (c_tp + c_fp) > 0 else 0.0
        recall = round(c_tp / (c_tp + c_fn), 4) if (c_tp + c_fn) > 0 else 0.0
        f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0
        per_insight[itype] = {
            "true_positives": c_tp,
            "false_positives": c_fp,
            "false_negatives": c_fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        }

    eval_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_test_cases": total,
        "correct_predictions": correct_count,
        "overall_accuracy": accuracy,
        "average_latency_ms": avg_latency,
        "failure_breakdown": dict(failure_types),
        "per_insight_metrics": per_insight,
        "detailed_results": detailed_results,
    }

    # Write results/eval.json
    output_json_path = os.path.join(results_dir, "eval.json")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    # Format Markdown summary table
    md_lines = [
        "# Router Evaluation Benchmark Summary",
        "",
        f"- **Total Test Cases:** {total}",
        f"- **Correct Predictions:** {correct_count}",
        f"- **Overall Accuracy:** {accuracy * 100:.2f}%",
        f"- **Average Latency:** {avg_latency:.2f} ms",
        f"- **Failure Types:** {dict(failure_types) or 'None'}",
        "",
        "## Performance per Insight Route",
        "",
        "| Insight Route | TP | FP | FN | Precision | Recall | F1 Score |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for itype, m in per_insight.items():
        md_lines.append(
            f"| `{itype}` | {m['true_positives']} | {m['false_positives']} | {m['false_negatives']} | "
            f"{m['precision']:.2f} | {m['recall']:.2f} | {m['f1_score']:.2f} |"
        )

    md_lines.extend([
        "",
        "## Sample Test Case Results",
        "",
        "| ID | Dataset | Question Snippet | Expected | Predicted | Status |",
        "| :-: | :--- | :--- | :--- | :--- | :-: |",
    ])
    for item in detailed_results[:10]:
        q_snippet = item["question"][:45] + ("..." if len(item["question"]) > 45 else "")
        status = "PASS" if item["correct"] else "FAIL"
        md_lines.append(
            f"| {item['id']} | `{item['dataset']}` | {q_snippet} | `{item['expected_route']}` | `{item['predicted_route']}` | {status} |"
        )

    md_table = "\n".join(md_lines)
    output_md_path = os.path.join(results_dir, "eval_summary.md")
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_table)

    # Safely print to stdout regardless of terminal encoding
    try:
        print("\n" + md_table + "\n")
    except UnicodeEncodeError:
        print("\n" + md_table.encode("ascii", "replace").decode("ascii") + "\n")

    print(f"Results written to:\n  - {output_json_path}\n  - {output_md_path}")
    return eval_report


if __name__ == "__main__":
    run_evaluation()
