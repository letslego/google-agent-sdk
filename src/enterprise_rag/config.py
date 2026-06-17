from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    model: str = os.getenv("RAG_MODEL", "gemini-2.5-flash")
    top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    vector_db_path: Path = Path(os.getenv("RAG_VECTOR_DB_PATH", "./chromadb"))
    structured_data_dir: Path = Path("./data/samples/structured")
    unstructured_data_dir: Path = Path("./data/samples/unstructured")


settings = Settings()

