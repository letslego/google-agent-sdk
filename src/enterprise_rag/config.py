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
    vertex_rerank_model: str = os.getenv("VERTEX_RERANK_MODEL", "gemini-2.5-flash")
    vertex_rerank_min_score: float = float(os.getenv("VERTEX_RERANK_MIN_SCORE", "0.45"))
    vertex_rerank_high_confidence_score: float = float(
        os.getenv("VERTEX_RERANK_HIGH_CONFIDENCE_SCORE", "0.8")
    )
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    gcp_location: str = os.getenv("GCP_LOCATION", "us-central1")
    enable_bigquery_ingestion: bool = (
        os.getenv("RAG_ENABLE_BIGQUERY_INGESTION", "false").lower() == "true"
    )
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "")
    bigquery_tables: str = os.getenv("BIGQUERY_TABLES", "")
    bigquery_limit_per_table: int = int(os.getenv("BIGQUERY_LIMIT_PER_TABLE", "500"))
    bigquery_partition_column: str = os.getenv("BIGQUERY_PARTITION_COLUMN", "")
    bigquery_partition_start: str = os.getenv("BIGQUERY_PARTITION_START", "")
    bigquery_partition_end: str = os.getenv("BIGQUERY_PARTITION_END", "")
    bigquery_use_incremental_checkpoint: bool = (
        os.getenv("BIGQUERY_USE_INCREMENTAL_CHECKPOINT", "true").lower() == "true"
    )
    bigquery_checkpoint_path: Path = Path(
        os.getenv("BIGQUERY_CHECKPOINT_PATH", "./logs/bq_ingestion_checkpoint.json")
    )
    groundedness_min_pass_rate: float = float(os.getenv("GROUNDEDNESS_MIN_PASS_RATE", "0.67"))
    vector_db_path: Path = Path(os.getenv("RAG_VECTOR_DB_PATH", "./chromadb"))
    structured_data_dir: Path = Path("./data/samples/structured")
    unstructured_data_dir: Path = Path("./data/samples/unstructured")


settings = Settings()

