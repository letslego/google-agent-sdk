from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from enterprise_rag.config import settings
from enterprise_rag.models import Document, RetrievalResult
from enterprise_rag.retrieval.vector_store import VectorStore


class HybridRetriever:
    def __init__(self, vector_store: VectorStore, enable_vector_search: bool = False):
        self.vector_store = vector_store
        self.enable_vector_search = enable_vector_search
        self.lexical_documents: list[Document] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.document_matrix = None
        self._vertex_reranker = None

    def _get_vertex_reranker(self):
        if not settings.enable_vertex_rerank:
            return None
        if self._vertex_reranker is not None:
            return self._vertex_reranker
        if not settings.gcp_project_id:
            return None
        try:
            from enterprise_rag.retrieval.vertex_reranker import VertexCrossEncoderReranker

            self._vertex_reranker = VertexCrossEncoderReranker(
                project_id=settings.gcp_project_id,
                location=settings.gcp_location,
                model_name=settings.vertex_rerank_model,
                min_score=settings.vertex_rerank_min_score,
                high_confidence_score=settings.vertex_rerank_high_confidence_score,
            )
        except Exception:
            self._vertex_reranker = None
        return self._vertex_reranker

    def build_lexical_index(self, documents: list[Document]) -> None:
        self.lexical_documents = documents
        corpus = [d.text for d in documents] or [""]
        self.document_matrix = self.vectorizer.fit_transform(corpus)

    def _lexical_query(self, query_text: str, top_k: int = 5) -> list[RetrievalResult]:
        if not self.lexical_documents or self.document_matrix is None:
            return []
        query_vec = self.vectorizer.transform([query_text])
        scores = cosine_similarity(query_vec, self.document_matrix).flatten()
        ranked_idx = np.argsort(scores)[::-1][:top_k]

        return [
            RetrievalResult(
                document=self.lexical_documents[i],
                score=float(scores[i]),
                source="lexical",
            )
            for i in ranked_idx
            if scores[i] > 0
        ]

    def search(
        self,
        query_text: str,
        top_k: int = 5,
        customer_id: str | None = None,
    ) -> list[RetrievalResult]:
        metadata_filter = {"customer_id": str(customer_id)} if customer_id else None
        vector_results: list[RetrievalResult] = []
        if self.enable_vector_search:
            try:
                vector_results = self.vector_store.query(
                    query_text=query_text,
                    top_k=top_k * 2,
                    metadata_filter=metadata_filter,
                )
            except Exception:
                # Keep the app responsive even if vector embedding backend is unavailable.
                vector_results = []
        lexical_results = self._lexical_query(query_text=query_text, top_k=top_k * 2)

        # Reciprocal rank fusion for robust hybrid ranking.
        combined_scores = defaultdict(float)
        result_map: dict[str, RetrievalResult] = {}

        for rank, result in enumerate(vector_results, start=1):
            combined_scores[result.document.id] += 1.0 / (60 + rank)
            result_map[result.document.id] = result

        for rank, result in enumerate(lexical_results, start=1):
            combined_scores[result.document.id] += 1.0 / (60 + rank)
            if result.document.id not in result_map:
                result_map[result.document.id] = result

        ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        base_results = [
            RetrievalResult(
                document=result_map[doc_id].document,
                score=score,
                source="hybrid",
            )
            for doc_id, score in ranked
        ]
        reranker = self._get_vertex_reranker()
        if reranker is None:
            return base_results
        try:
            return reranker.rerank(query=query_text, candidates=base_results, top_k=top_k)
        except Exception:
            return base_results

