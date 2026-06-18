from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json

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
    partition_column: str = "",
    partition_start: str = "",
    partition_end: str = "",
    use_incremental_checkpoint: bool = True,
    checkpoint_path: Path = Path("./logs/bq_ingestion_checkpoint.json"),
) -> list[Document]:
    """
    Loads enterprise structured records from BigQuery tables and transforms each row
    into retrieval-ready documents.
    """
    if not project_id or not dataset or not tables:
        return []

    client = bigquery.Client(project=project_id)
    documents: list[Document] = []
    checkpoints = _load_checkpoint(checkpoint_path)
    checkpoint_updated = False

    for table in tables:
        table_ref = f"`{project_id}.{dataset}.{table}`"
        table_key = f"{project_id}.{dataset}.{table}"
        filters = []
        query_params: list[bigquery.ScalarQueryParameter] = []

        lower_bound = partition_start.strip() if partition_start else ""
        if use_incremental_checkpoint and partition_column:
            last_checkpoint = checkpoints.get(table_key, {}).get("last_partition_value", "")
            if last_checkpoint:
                lower_bound = last_checkpoint

        if partition_column:
            if lower_bound:
                filters.append(f"CAST({partition_column} AS STRING) > @partition_start")
                query_params.append(
                    bigquery.ScalarQueryParameter("partition_start", "STRING", lower_bound)
                )
            if partition_end:
                filters.append(f"CAST({partition_column} AS STRING) <= @partition_end")
                query_params.append(
                    bigquery.ScalarQueryParameter("partition_end", "STRING", partition_end)
                )

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        query = f"SELECT * FROM {table_ref} {where_clause} LIMIT {int(limit_per_table)}"
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        rows = list(client.query(query, job_config=job_config).result())
        table_partition_values: list[str] = []

        for idx, row in enumerate(rows):
            row_dict = dict(row.items())
            customer_id = row_dict.get("customer_id")
            partition_value = str(row_dict.get(partition_column, "")) if partition_column else ""
            if partition_value:
                table_partition_values.append(partition_value)
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

        if use_incremental_checkpoint and partition_column and table_partition_values:
            latest_partition = max(table_partition_values)
            checkpoints[table_key] = {
                "last_partition_value": latest_partition,
                "updated_at_utc": datetime.now(UTC).isoformat(),
            }
            checkpoint_updated = True

    if checkpoint_updated:
        _save_checkpoint(checkpoint_path, checkpoints)

    return documents


def _load_checkpoint(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_checkpoint(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

