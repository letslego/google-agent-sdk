from __future__ import annotations

from google.cloud import bigquery

from enterprise_rag.models import Document


def _row_to_text(table_name: str, row: dict) -> str:
    payload = ", ".join([f"{k}={v}" for k, v in row.items()])
    return f"Structured record from BigQuery table {table_name}: {payload}"


def load_bigquery_documents(
    *,
    project_id: str,
    dataset: str,
    tables: list[str],
    limit_per_table: int = 500,
) -> list[Document]:
    """
    Loads enterprise structured records from BigQuery tables and transforms each row
    into retrieval-ready documents.
    """
    if not project_id or not dataset or not tables:
        return []

    client = bigquery.Client(project=project_id)
    documents: list[Document] = []

    for table in tables:
        table_ref = f"`{project_id}.{dataset}.{table}`"
        query = f"SELECT * FROM {table_ref} LIMIT {int(limit_per_table)}"
        rows = list(client.query(query).result())

        for idx, row in enumerate(rows):
            row_dict = dict(row.items())
            customer_id = row_dict.get("customer_id")
            documents.append(
                Document(
                    id=f"bq-{table}-{idx}",
                    text=_row_to_text(table, row_dict),
                    metadata={
                        "source_type": "structured",
                        "table": table,
                        "row_id": idx,
                        "customer_id": str(customer_id) if customer_id is not None else None,
                        "path": f"bigquery://{project_id}.{dataset}.{table}",
                    },
                )
            )
    return documents

