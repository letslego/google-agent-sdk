from pathlib import Path
import pandas as pd

from enterprise_rag.models import Document


def load_structured_documents(data_dir: Path) -> list[Document]:
    """
    Reads tabular enterprise data and transforms each row into a retrieval-ready
    text document with rich metadata.
    """
    documents: list[Document] = []

    for csv_path in sorted(data_dir.glob("*.csv")):
        df = pd.read_csv(csv_path)
        table_name = csv_path.stem

        for idx, row in df.iterrows():
            payload = ", ".join([f"{col}={row[col]}" for col in df.columns])
            text = f"Structured record from {table_name}: {payload}"
            doc_id = f"{table_name}-{idx}"
            metadata = {
                "source_type": "structured",
                "table": table_name,
                "row_id": idx,
                "customer_id": str(row["customer_id"]) if "customer_id" in df.columns else None,
                "path": str(csv_path),
            }
            documents.append(Document(id=doc_id, text=text, metadata=metadata))

    return documents

