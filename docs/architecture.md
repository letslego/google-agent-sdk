# Enterprise RAG Architecture

```text
                +-----------------------------+
                | Structured Enterprise Data  |
                | (CRM, Tickets, Billing CSV) |
                +--------------+--------------+
                               |
                +--------------v--------------+
                | Unstructured Data Sources   |
                | (Policies, KB, PDFs, DOCX)  |
                +--------------+--------------+
                               |
                               v
                  +--------------------------+
                  | Ingestion + Chunking     |
                  | Metadata enrichment      |
                  +-------------+------------+
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v
          +-------------------+   +--------------------+
          | Chroma Vector DB  |   | Lexical TF-IDF     |
          | semantic index     |   | keyword index      |
          +---------+---------+   +----------+---------+
                    \                 /
                     \               /
                      v             v
                     +---------------+
                     | Hybrid Search |
                     | (RRF fusion)  |
                     +-------+-------+
                             |
                             v
                +----------------------------+
                | Google ADK Agent + Tool   |
                | grounded answer + citation |
                +----------------------------+
```

