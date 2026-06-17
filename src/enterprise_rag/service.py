from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from enterprise_rag.ingestion.pipeline import EnterpriseRAGPipeline
from enterprise_rag.models import RetrievalResult
from enterprise_rag.skills_registry import search_skills
from enterprise_rag.tracing import append_trace


@dataclass
class QueryResponse:
    answer: str
    context: str
    trace: dict


class RAGService:
    def __init__(self):
        self.pipeline = EnterpriseRAGPipeline()
        self.pipeline.ingest()

    def answer_query(
        self,
        query: str,
        customer_id: str | None = None,
        top_k: int | None = None,
    ) -> QueryResponse:
        started = perf_counter()

        skill_matches = search_skills(query=query, limit=1)
        selected_skill = skill_matches[0] if skill_matches else None
        retrieval_results = self.pipeline.retrieve(
            query=query,
            customer_id=customer_id,
            top_k=top_k,
        )
        context = self.pipeline.format_results(retrieval_results)

        answer = self._build_answer(query, retrieval_results, selected_skill.name if selected_skill else None)
        latency_ms = round((perf_counter() - started) * 1000, 2)

        trace_payload = append_trace(
            {
                "query": query,
                "customer_id": customer_id or "",
                "top_k": top_k,
                "selected_skill": selected_skill.skill_id if selected_skill else "",
                "latency_ms": latency_ms,
                "steps": [
                    "search_skill_registry",
                    "use_skill" if selected_skill else "use_skill_skipped",
                    "retrieve_enterprise_context",
                    "compose_answer",
                ],
                "retrieved_sources": [
                    item.document.metadata.get("path", "unknown") for item in retrieval_results
                ],
                "answer": answer,
            }
        )
        return QueryResponse(answer=answer, context=context, trace=trace_payload)

    @staticmethod
    def _build_answer(
        query: str,
        results: list[RetrievalResult],
        skill_name: str | None,
    ) -> str:
        if not results:
            return (
                "I could not find relevant enterprise evidence for this query. "
                "Please provide additional customer details or ingest more source data."
            )

        action = (
            f"Selected operational playbook: {skill_name}."
            if skill_name
            else "No specific playbook matched; using standard support workflow."
        )
        evidence = []
        for idx, item in enumerate(results[:3], start=1):
            snippet = item.document.text.replace("\n", " ")[:180].strip()
            evidence.append(f"[{idx}] {snippet}")

        return (
            f"Query focus: {query}\n"
            f"{action}\n"
            "Grounded evidence:\n"
            + "\n".join(evidence)
            + "\nRecommended next step: respond to the customer with cited evidence and concrete timeline commitments."
        )

