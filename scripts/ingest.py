from enterprise_rag.ingestion.pipeline import EnterpriseRAGPipeline


def main() -> None:
    pipeline = EnterpriseRAGPipeline()
    count = pipeline.ingest()
    print(f"Ingested {count} enterprise documents/chunks into the vector + lexical indexes.")


if __name__ == "__main__":
    main()

