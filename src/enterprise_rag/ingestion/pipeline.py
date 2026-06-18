from enterprise_rag.config import settings
from enterprise_rag.connectors.bigquery_loader import load_bigquery_documents
from enterprise_rag.connectors.structured_loader import load_structured_documents
from enterprise_rag.connectors.unstructured_loader import load_unstructured_documents
from enterprise_rag.models import Document, RetrievalResult
from enterprise_rag.retrieval.hybrid_retriever import HybridRetriever
from enterprise_rag.retrieval.vector_store import VectorStore


class EnterpriseRAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore(settings.vector_db_path)
        self.retriever = HybridRetriever(
            self.vector_store,
            enable_vector_search=settings.enable_vector_search,
        )
        self._documents: list[Document] = []

    def ingest(self) -> int:
        structured_docs = load_structured_documents(settings.structured_data_dir)
        unstructured_docs = load_unstructured_documents(settings.unstructured_data_dir)
        bigquery_docs: list[Document] = []
        if settings.enable_bigquery_ingestion:
            tables = [t.strip() for t in settings.bigquery_tables.split(",") if t.strip()]
            try:
                bigquery_docs = load_bigquery_documents(
                    project_id=settings.gcp_project_id,
                    dataset=settings.bigquery_dataset,
                    tables=tables,
                    limit_per_table=settings.bigquery_limit_per_table,
                    partition_column=settings.bigquery_partition_column,
                    partition_start=settings.bigquery_partition_start,
                    partition_end=settings.bigquery_partition_end,
                    use_incremental_checkpoint=settings.bigquery_use_incremental_checkpoint,
                    checkpoint_path=settings.bigquery_checkpoint_path,
                )
            except Exception:
                # Keep local demos healthy even when BigQuery is not configured.
                bigquery_docs = []

        all_docs = structured_docs + unstructured_docs + bigquery_docs

        if settings.enable_vector_search:
            try:
                self.vector_store.upsert(all_docs)
            except Exception:
                # Fallback mode keeps lexical retrieval available for local demos.
                pass
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

