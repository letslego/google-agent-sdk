# Google ADK Enterprise RAG Pipeline

A production-style **Retrieval-Augmented Generation (RAG)** starter project that demonstrates how to use **Google ADK** to answer customer questions from both:

- **Structured enterprise data** (CRM records, support tickets, billing-style tables)
- **Unstructured enterprise content** (policies, knowledge base, docs, PDFs, DOCX)

This repository is designed for customer support and customer success scenarios where responses must be grounded in enterprise truth and include source-backed context.

## What This RAG Pipeline Does

When a customer asks a question, the system:

1. Ingests and normalizes enterprise data from structured and unstructured sources.
2. Enriches each chunk/record with metadata (source path, table name, customer_id, chunk_id).
3. Indexes content into:
   - a **vector store** (semantic retrieval via Chroma), and
   - a **lexical store** (keyword retrieval via TF-IDF).
4. Runs **hybrid retrieval** (reciprocal rank fusion) for high recall + precision.
5. Feeds grounded context to a **Google ADK agent tool**.
6. Produces an answer with evidence-oriented behavior and citations.

## Included Features

- Multi-source ingestion for enterprise data domains
- Chunking strategy for long unstructured documents
- Metadata-aware filtering (`customer_id`-scoped retrieval)
- Hybrid retrieval (semantic + lexical fusion)
- ADK tool-based grounding pattern (`retrieve_enterprise_context`)
- FastAPI retrieval endpoint for service integration
- Sample datasets for immediate local demo
- Architecture documentation and Makefile automation

## Repository Layout

```text
google-adk-enterprise-rag/
├── data/samples/
│   ├── structured/            # CSV enterprise records
│   └── unstructured/          # Policies / KB text
├── docs/
│   └── architecture.md
├── scripts/
│   └── ingest.py
├── src/enterprise_rag/
│   ├── adk_agent/agent.py     # Google ADK root agent + tool
│   ├── connectors/            # Structured/unstructured loaders
│   ├── ingestion/pipeline.py  # End-to-end ingest + retrieve
│   ├── retrieval/             # Vector + hybrid retrieval logic
│   └── app.py                 # FastAPI service
├── .env.example
├── Makefile
└── pyproject.toml
```

## Quick Start

### 1) Create environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

### 2) Configure environment variables

```bash
cp .env.example .env
```

Set your `GOOGLE_API_KEY` in `.env`.

### 3) Ingest enterprise data

```bash
make ingest
```

### 4) Run the ADK agent

```bash
make run-adk
```

Alternative ADK web UI:

```bash
adk web src/enterprise_rag/adk_agent
```

### 5) Optional: run retrieval API

```bash
make run-api
```

Sample request:

```bash
curl -X POST http://127.0.0.1:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query":"What SLA and response policy applies to Acme Health latency issue?",
    "customer_id":"C1001",
    "top_k":5
  }'
```

## Example Customer Queries

- "My Claim API is slow for Acme Health. What support policy applies and what are the required update intervals?"
- "For customer C1002, what is the current ticket status and likely billing reconciliation steps?"
- "For Nimbus Logistics webhook retries, what mitigation guidance is documented?"

## Extending to Real Enterprise Data

Replace sample loaders with connectors to:

- Data warehouses (BigQuery, Snowflake, Databricks)
- Operational DBs (Postgres, SQL Server, Oracle)
- Ticketing systems (ServiceNow, Jira, Zendesk)
- Knowledge platforms (Confluence, SharePoint, Drive)

Recommended production upgrades:

- PII redaction and access policy enforcement per tenant
- Re-ranker model for final context ordering
- Query rewriting and intent routing agent
- Response schema validation and confidence scoring
- Evaluation harness (answer quality, grounding, latency)
- Observability dashboards and trace collection

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## GitHub: Create and Push a New Repository

From this project root:

```bash
git init
git add .
git commit -m "Initial commit: enterprise RAG pipeline with Google ADK"
gh repo create google-adk-enterprise-rag --public --source=. --remote=origin --push
```

If you prefer private visibility:

```bash
gh repo create google-adk-enterprise-rag --private --source=. --remote=origin --push
```

## Why This Is Useful for Customer Query Answering

This pipeline combines enterprise tabular truth with policy and KB narrative context. The result is a support agent that can answer customer questions with:

- Better factual grounding
- Better handling of account-specific context
- Better explainability via source-backed responses

---

If you want, I can next add:

- a BigQuery connector,
- reranking with Vertex AI embeddings/ranker,
- and an evaluation script with pass/fail groundedness checks.
