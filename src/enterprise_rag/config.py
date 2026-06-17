from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    model: str = os.getenv("RAG_MODEL", "gemini-2.5-flash")
    top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    enable_vector_search: bool = os.getenv("RAG_ENABLE_VECTOR_SEARCH", "false").lower() == "true"
    enable_vertex_rerank: bool = os.getenv("RAG_ENABLE_VERTEX_RERANK", "false").lower() == "true"
    vertex_embedding_model: str = os.getenv("VERTEX_EMBEDDING_MODEL", "text-embedding-005")
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    gcp_location: str = os.getenv("GCP_LOCATION", "us-central1")
    enable_bigquery_ingestion: bool = (
        os.getenv("RAG_ENABLE_BIGQUERY_INGESTION", "false").lower() == "true"
    )
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "")
    bigquery_tables: str = os.getenv("BIGQUERY_TABLES", "")
    bigquery_limit_per_table: int = int(os.getenv("BIGQUERY_LIMIT_PER_TABLE", "500"))
    vector_db_path: Path = Path(os.getenv("RAG_VECTOR_DB_PATH", "./chromadb"))
    structured_data_dir: Path = Path("./data/samples/structured")
    unstructured_data_dir: Path = Path("./data/samples/unstructured")


settings = Settings()

