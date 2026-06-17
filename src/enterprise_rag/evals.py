from __future__ import annotations

from pathlib import Path
import json

from enterprise_rag.service import RAGService


EVAL_CASES_PATH = Path("data/evals/eval_cases.json")


def load_eval_cases() -> list[dict]:
    if not EVAL_CASES_PATH.exists():
        return []
    return json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))


def run_eval_suite(service: RAGService) -> list[dict]:
    cases = load_eval_cases()
    results: list[dict] = []

    for case in cases:
        response = service.answer_query(
            query=case["query"],
            customer_id=case.get("customer_id"),
            top_k=case.get("top_k"),
        )
        answer_lower = response.answer.lower()
        expected = [term.lower() for term in case.get("expected_keywords", [])]
        matched = [term for term in expected if term in answer_lower]
        pass_rate = (len(matched) / len(expected)) if expected else 1.0
        passed = pass_rate >= case.get("min_keyword_hit_rate", 0.5)

        results.append(
            {
                "case_id": case.get("case_id", ""),
                "query": case["query"],
                "customer_id": case.get("customer_id", ""),
                "latency_ms": response.trace.get("latency_ms", 0),
                "expected_keywords": ", ".join(expected),
                "matched_keywords": ", ".join(matched),
                "keyword_hit_rate": round(pass_rate, 2),
                "passed": passed,
            }
        )
    return results

