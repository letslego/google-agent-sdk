from __future__ import annotations

from dataclasses import dataclass
import json

from enterprise_rag.models import RetrievalResult


@dataclass
class VertexCrossEncoderReranker:
    project_id: str
    location: str
    model_name: str = "gemini-2.5-flash"
    min_score: float = 0.45
    high_confidence_score: float = 0.8

    def __post_init__(self) -> None:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=self.project_id, location=self.location)
        self._model = GenerativeModel(self.model_name)

    def _score_pair(self, query: str, document: str) -> float:
        prompt = (
            "You are a relevance scoring cross-encoder.\n"
            "Given QUERY and DOCUMENT, output JSON only with this schema: "
            '{"score": <float between 0 and 1>}.\n'
            "Use semantic and factual relevance where 1.0 is highly relevant.\n\n"
            f"QUERY:\n{query}\n\nDOCUMENT:\n{document[:3000]}"
        )
        response = self._model.generate_content(prompt)
        text = (response.text or "").strip()
        if not text:
            return 0.0
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        try:
            payload = json.loads(text)
            score = float(payload.get("score", 0.0))
        except Exception:
            score = 0.0
        return max(0.0, min(1.0, score))

    def _calibrate(self, raw_score: float) -> float:
        if raw_score < self.min_score:
            return 0.0
        calibrated = (raw_score - self.min_score) / max(1e-6, (1.0 - self.min_score))
        if raw_score >= self.high_confidence_score:
            calibrated = min(1.0, calibrated + 0.05)
        return max(0.0, min(1.0, calibrated))

    def rerank(self, query: str, candidates: list[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        if not candidates:
            return []

        rescored: list[RetrievalResult] = []
        for candidate in candidates:
            raw_score = self._score_pair(query=query, document=candidate.document.text)
            calibrated_score = self._calibrate(raw_score)
            if calibrated_score <= 0:
                continue
            rescored.append(
                RetrievalResult(
                    document=candidate.document,
                    score=float(calibrated_score),
                    source="vertex_cross_encoder_rerank",
                )
            )

        if not rescored:
            # Fallback avoids empty result sets if all candidates are below threshold.
            rescored = [
                RetrievalResult(
                    document=item.document,
                    score=item.score,
                    source="hybrid_fallback",
                )
                for item in candidates
            ]
        rescored.sort(key=lambda r: r.score, reverse=True)
        return rescored[:top_k]

