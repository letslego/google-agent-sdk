from enterprise_rag.config import settings
from enterprise_rag.connectors.structured_loader import load_structured_documents
from enterprise_rag.connectors.unstructured_loader import load_unstructured_documents
from enterprise_rag.models import Document, RetrievalResult
from enterprise_rag.retrieval.hybrid_retriever import HybridRetriever
from enterprise_rag.retrieval.vector_store import VectorStore


class EnterpriseRAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore(settings.vector_db_path)
        self.retriever = HybridRetriever(self.vector_store)
        self._documents: list[Document] = []

    def ingest(self) -> int:
        structured_docs = load_structured_documents(settings.structured_data_dir)
        unstructured_docs = load_unstructured_documents(settings.unstructured_data_dir)
        all_docs = structured_docs + unstructured_docs

        self.vector_store.upsert(all_docs)
        self.retriever.build_lexical_index(all_docs)
        self._documents = all_docs
        return len(all_docs)

    def retrieve_context(
        self,
        query: str,
        customer_id: str | None = None,
        top_k: int | None = None,
    ) -> str:
        results = self.retrieve(query=query, customer_id=customer_id, top_k=top_k)
        return self.format_results(results)

    def retrieve(
        self,
        query: str,
        customer_id: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        k = top_k or settings.top_k
        return self.retriever.search(query_text=query, top_k=k, customer_id=customer_id)

    @staticmethod
    def format_results(results: list[RetrievalResult]) -> str:
        if not results:
            return "No relevant enterprise context found."

        lines: list[str] = []
        for idx, result in enumerate(results, start=1):
            source_ref = result.document.metadata.get("path", "unknown")
            lines.append(
                f"[{idx}] score={result.score:.4f} source={source_ref}\n{result.document.text}"
            )
        return "\n\n".join(lines)

