from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from enterprise_rag.models import RetrievalResult


@dataclass
class VertexReranker:
    project_id: str
    location: str
    model_name: str = "text-embedding-005"

    def __post_init__(self) -> None:
        import vertexai
        from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

        self._text_embedding_input = TextEmbeddingInput
        self._embedding_model_cls = TextEmbeddingModel
        vertexai.init(project=self.project_id, location=self.location)
        self._model = self._embedding_model_cls.from_pretrained(self.model_name)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _embed_query(self, query: str) -> list[float]:
        query_input = self._text_embedding_input(text=query, task_type="RETRIEVAL_QUERY")
        embedding = self._model.get_embeddings([query_input])[0]
        return embedding.values

    def _embed_documents(self, texts: list[str]) -> list[list[float]]:
        doc_inputs = [self._text_embedding_input(text=t, task_type="RETRIEVAL_DOCUMENT") for t in texts]
        embeddings = self._model.get_embeddings(doc_inputs)
        return [item.values for item in embeddings]

    def rerank(self, query: str, candidates: list[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        if not candidates:
            return []

        query_emb = self._embed_query(query)
        doc_embs = self._embed_documents([c.document.text for c in candidates])
        rescored: list[RetrievalResult] = []
        for candidate, doc_emb in zip(candidates, doc_embs):
            score = self._cosine_similarity(query_emb, doc_emb)
            rescored.append(
                RetrievalResult(
                    document=candidate.document,
                    score=float(score),
                    source="vertex_rerank",
                )
            )
        rescored.sort(key=lambda r: r.score, reverse=True)
        return rescored[:top_k]

