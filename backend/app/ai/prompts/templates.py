from dataclasses import dataclass

from app.ai.exceptions import AITemplateNotFoundError


@dataclass(frozen=True)
class PromptTemplate:
    """A reusable, named prompt shape — the system instruction plus a user-message template
    with named `{placeholder}` slots. Capabilities render one of these against an AIContext
    instead of building prompt strings inline in a router or service, so prompt wording lives
    in one place and can be tuned without touching call sites."""

    id: str
    system_prompt: str
    user_template: str

    def render(self, **kwargs: str) -> str:
        return self.user_template.format(**kwargs)


INCIDENT_EXPLANATION = PromptTemplate(
    id="incident_explanation",
    system_prompt=(
        "You are a safety engineering assistant for an industrial refinery. Explain incidents "
        "factually, using only the operational context supplied below. Never invent a root "
        "cause, sensor reading, or timeline event that isn't present in the context, and say so "
        "plainly if the context is insufficient to answer."
    ),
    user_template=(
        "Using the operational context below, explain why this incident occurred, how it "
        "progressed, and how it was handled.\n\n{context}"
    ),
)

RECOMMENDATION_EXPLANATION = PromptTemplate(
    id="recommendation_explanation",
    system_prompt=(
        "You are a safety engineering assistant for an industrial refinery. Explain why a "
        "recommendation was issued, grounded only in the supplied context — never invent a "
        "justification the context doesn't support."
    ),
    user_template="Using the context below, explain why this recommendation was issued and what it addresses.\n\n{context}",
)

ANALYTICS_QA = PromptTemplate(
    id="analytics_qa",
    system_prompt=(
        "You are a safety analytics assistant for an industrial refinery. Answer the operator's "
        "question using only the analytics context supplied. If the context doesn't contain "
        "enough information to answer, say so instead of guessing."
    ),
    user_template="Question: {question}\n\nAnalytics context:\n{context}",
)

REPORT_SUMMARY = PromptTemplate(
    id="report_summary",
    system_prompt=(
        "You are a safety reporting assistant for an industrial refinery. Summarize the "
        "supplied report data for a plant manager in plain, factual language — no speculation "
        "beyond what the data shows."
    ),
    user_template="Summarize the following safety analytics report.\n\n{context}",
)

SOP_LOOKUP = PromptTemplate(
    id="sop_lookup",
    system_prompt=(
        "You are a safety procedures assistant for an industrial refinery. Answer using only "
        "the supplied procedure excerpts — quote or closely paraphrase them, and say so if the "
        "excerpts don't cover the question. Never invent a procedure step."
    ),
    user_template="Question: {question}\n\nRelevant procedure excerpts:\n{context}",
)

_REGISTRY: dict[str, PromptTemplate] = {
    template.id: template
    for template in (
        INCIDENT_EXPLANATION,
        RECOMMENDATION_EXPLANATION,
        ANALYTICS_QA,
        REPORT_SUMMARY,
        SOP_LOOKUP,
    )
}


def get_template(template_id: str) -> PromptTemplate:
    try:
        return _REGISTRY[template_id]
    except KeyError:
        raise AITemplateNotFoundError(f"Unknown prompt template: {template_id!r}") from None
