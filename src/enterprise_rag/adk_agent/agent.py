from google.adk.agents import Agent

from enterprise_rag.config import settings
from enterprise_rag.ingestion.pipeline import EnterpriseRAGPipeline


pipeline = EnterpriseRAGPipeline()
pipeline.ingest()


def retrieve_enterprise_context(query: str, customer_id: str = "") -> str:
    """
    Tool exposed to ADK agent:
    - query: customer's natural language question
    - customer_id: optional filter to narrow context to one enterprise customer
    """
    cid = customer_id.strip() or None
    return pipeline.retrieve_context(query=query, customer_id=cid)


root_agent = Agent(
    name="enterprise_rag_agent",
    model=settings.model,
    description="Answers customer queries using enterprise structured and unstructured data.",
    instruction=(
        "You are an enterprise customer support AI. "
        "Always call retrieve_enterprise_context before answering. "
        "Ground your final response only in retrieved context. "
        "If evidence is missing, explicitly say what data is missing. "
        "Include citations in [n] format tied to retrieved snippets."
    ),
    tools=[retrieve_enterprise_context],
)

