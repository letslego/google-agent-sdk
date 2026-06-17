from fastapi import FastAPI
from pydantic import BaseModel

from enterprise_rag.ingestion.pipeline import EnterpriseRAGPipeline


class QueryRequest(BaseModel):
    query: str
    customer_id: str | None = None
    top_k: int | None = None


app = FastAPI(title="Enterprise RAG API", version="0.1.0")
pipeline = EnterpriseRAGPipeline()
pipeline.ingest()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/retrieve")
def retrieve(request: QueryRequest) -> dict[str, str]:
    context = pipeline.retrieve_context(
        query=request.query,
        customer_id=request.customer_id,
        top_k=request.top_k,
    )
    return {"context": context}

