from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json

from enterprise_rag.evals import load_eval_cases
from enterprise_rag.service import RAGService


OUTPUT_PATH = Path("logs/groundedness_eval_results.json")


def _extract_context_lines(context: str) -> list[str]:
    chunks = []
    for part in context.split("\n\n"):
        cleaned = part.strip()
        if not cleaned:
            continue
        if "\n" in cleaned:
            chunks.append(cleaned.split("\n", 1)[1].lower())
        else:
            chunks.append(cleaned.lower())
    return chunks


def _compute_groundedness(answer: str, context: str) -> tuple[float, bool, dict]:
    answer_lines = [line.strip().lower() for line in answer.splitlines() if line.strip()]
    context_chunks = _extract_context_lines(context)
    if not answer_lines or not context_chunks:
        return 0.0, False, {"supported_lines": 0, "total_lines": len(answer_lines)}

    supported = 0
    for line in answer_lines:
        if line.startswith("query focus:") or line.startswith("recommended next step:"):
            continue
        if any(token in chunk for chunk in context_chunks for token in line.split() if len(token) > 4):
            supported += 1

    total = max(1, len([l for l in answer_lines if len(l.split()) >= 3]))
    score = supported / total
    passed = score >= 0.5
    return round(score, 2), passed, {"supported_lines": supported, "total_lines": total}


def main() -> None:
    service = RAGService()
    cases = load_eval_cases()
    results = []

    for case in cases:
        response = service.answer_query(
            query=case["query"],
            customer_id=case.get("customer_id"),
            top_k=case.get("top_k"),
        )
        groundedness_score, grounded_pass, details = _compute_groundedness(
            response.answer,
            response.context,
        )
        result = {
            "case_id": case.get("case_id", ""),
            "query": case["query"],
            "customer_id": case.get("customer_id", ""),
            "groundedness_score": groundedness_score,
            "grounded_pass": grounded_pass,
            "groundedness_details": details,
            "latency_ms": response.trace.get("latency_ms", 0),
            "selected_skill": response.trace.get("selected_skill", ""),
            "trace_id": response.trace.get("trace_id", ""),
        }
        results.append(result)
        print(
            f"{result['case_id']}: pass={result['grounded_pass']} "
            f"score={result['groundedness_score']} latency_ms={result['latency_ms']}"
        )

    summary = {
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "total_cases": len(results),
        "pass_count": sum(1 for r in results if r["grounded_pass"]),
        "pass_rate": round(
            (sum(1 for r in results if r["grounded_pass"]) / len(results)) if results else 0.0,
            2,
        ),
        "results": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nGroundedness evaluation written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

