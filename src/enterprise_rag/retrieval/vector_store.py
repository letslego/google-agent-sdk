from pathlib import Path
import chromadb

from enterprise_rag.models import Document, RetrievalResult


class VectorStore:
    def __init__(self, persist_path: Path, collection_name: str = "enterprise_docs"):
        self.client = chromadb.PersistentClient(path=str(persist_path))
        self.collection = self.client.get_or_create_collection(collection_name)

    def upsert(self, documents: list[Document]) -> None:
        if not documents:
            return
        self.collection.upsert(
            ids=[d.id for d in documents],
            documents=[d.text for d in documents],
            metadatas=[d.metadata for d in documents],
        )

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[RetrievalResult]:
        response = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=metadata_filter,
        )
        results: list[RetrievalResult] = []
        docs = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        ids = response.get("ids", [[]])[0]
        distances = response.get("distances", [[]])[0]

        for doc_id, text, metadata, distance in zip(ids, docs, metadatas, distances):
            score = 1.0 / (1.0 + float(distance))
            results.append(
                RetrievalResult(
                    document=Document(id=doc_id, text=text, metadata=metadata),
                    score=score,
                    source="vector",
                )
            )
        return results

