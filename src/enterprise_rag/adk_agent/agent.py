from google.adk.agents import Agent

from enterprise_rag.config import settings
from enterprise_rag.ingestion.pipeline import EnterpriseRAGPipeline
from enterprise_rag.skills_registry import get_skill, search_skills


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


def search_skill_registry(query: str, limit: int = 3) -> str:
    """
    Search available support skills by issue intent and keywords.
    Returns skill metadata that the agent can choose to use.
    """
    matches = search_skills(query=query, limit=limit)
    if not matches:
        return "No matching skills found."

    lines: list[str] = []
    for skill in matches:
        lines.append(
            f"- skill_id={skill.skill_id} | name={skill.name}\n"
            f"  description={skill.description}\n"
            f"  triggers={', '.join(skill.triggers)}"
        )
    return "\n".join(lines)


def use_skill(skill_id: str) -> str:
    """
    Fetch the operational playbook for a selected skill_id.
    """
    skill = get_skill(skill_id)
    if not skill:
        return f"Unknown skill_id: {skill_id}"

    steps = "\n".join([f"{idx}. {step}" for idx, step in enumerate(skill.playbook, start=1)])
    return (
        f"Using skill: {skill.name} ({skill.skill_id})\n"
        f"Description: {skill.description}\n"
        f"Playbook:\n{steps}"
    )


root_agent = Agent(
    name="enterprise_rag_agent",
    model=settings.model,
    description="Answers customer queries using enterprise structured and unstructured data.",
    instruction=(
        "You are an enterprise customer support AI. "
        "For each user query, first call search_skill_registry to discover relevant support skills. "
        "If a matching skill exists, call use_skill to load its playbook. "
        "Always call retrieve_enterprise_context before finalizing your answer. "
        "Ground your final response only in retrieved context. "
        "Combine skill playbook guidance with enterprise retrieved evidence. "
        "If evidence is missing, explicitly say what data is missing. "
        "Include citations in [n] format tied to retrieved snippets."
    ),
    tools=[search_skill_registry, use_skill, retrieve_enterprise_context],
)

