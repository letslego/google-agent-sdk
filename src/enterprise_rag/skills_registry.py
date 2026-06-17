from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    skill_id: str
    name: str
    description: str
    triggers: tuple[str, ...]
    playbook: tuple[str, ...]


SKILLS: tuple[Skill, ...] = (
    Skill(
        skill_id="sla_incident_response",
        name="SLA Incident Response",
        description="Handles high-priority API incidents with SLA-safe communications.",
        triggers=("latency", "sla", "p1", "incident", "api outage"),
        playbook=(
            "Classify severity and confirm customer impact.",
            "Open incident bridge and assign incident commander.",
            "Post customer status updates every 30 minutes.",
            "Publish mitigation summary and RCA timeline.",
        ),
    ),
    Skill(
        skill_id="billing_reconciliation",
        name="Billing Reconciliation",
        description="Guides invoice mismatch investigation and correction workflow.",
        triggers=("invoice", "billing", "overcharge", "usage mismatch", "vat"),
        playbook=(
            "Compare invoice line items against warehouse usage snapshots.",
            "Identify variance source (usage lag, tax, contract mapping).",
            "Issue corrected invoice and customer communication note.",
            "Capture preventive controls for next billing cycle.",
        ),
    ),
    Skill(
        skill_id="webhook_recovery",
        name="Webhook Delivery Recovery",
        description="Restores webhook delivery failures and validates retry behavior.",
        triggers=("webhook", "retries", "signature", "callback", "endpoint health"),
        playbook=(
            "Validate endpoint health and TLS/certificate status.",
            "Verify request signature validation logic.",
            "Replay failed events and monitor retry queue health.",
            "Confirm delivery SLO and close incident notes.",
        ),
    ),
)


def search_skills(query: str, limit: int = 3) -> list[Skill]:
    terms = set(query.lower().split())
    scored: list[tuple[int, Skill]] = []

    for skill in SKILLS:
        trigger_hits = sum(1 for t in skill.triggers if any(term in t for term in terms))
        name_hit = 1 if any(term in skill.name.lower() for term in terms) else 0
        description_hit = 1 if any(term in skill.description.lower() for term in terms) else 0
        score = (trigger_hits * 3) + (name_hit * 2) + description_hit
        if score > 0:
            scored.append((score, skill))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [skill for _, skill in scored[:limit]]


def get_skill(skill_id: str) -> Skill | None:
    for skill in SKILLS:
        if skill.skill_id == skill_id:
            return skill
    return None

