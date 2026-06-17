from fastapi import FastAPI
from pydantic import BaseModel

from enterprise_rag.service import RAGService
from enterprise_rag.tracing import read_traces


class QueryRequest(BaseModel):
    query: str
    customer_id: str | None = None
    top_k: int | None = None


app = FastAPI(title="Enterprise RAG API", version="0.1.0")
service = RAGService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/retrieve")
def retrieve(request: QueryRequest) -> dict[str, str]:
    response = service.answer_query(
        query=request.query,
        customer_id=request.customer_id,
        top_k=request.top_k,
    )
    return {"context": response.context}


@app.post("/query")
def query(request: QueryRequest) -> dict:
    response = service.answer_query(
        query=request.query,
        customer_id=request.customer_id,
        top_k=request.top_k,
    )
    return {
        "answer": response.answer,
        "context": response.context,
        "trace": response.trace,
    }


@app.get("/traces")
def traces(limit: int = 50) -> dict[str, list[dict]]:
    return {"items": read_traces(limit=limit)}

