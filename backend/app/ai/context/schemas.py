from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class AIContextScope(str, Enum):
    """What kind of entity a context was assembled around. Adding a new scope (zone,
    analytics_period, report) means adding one new value here plus one new
    `ContextBuilder.build_*_context` method — every downstream consumer (prompt templates,
    AIService, the API layer) is already scope-agnostic."""

    INCIDENT = "incident"


class ContextSection(BaseModel):
    """One labeled slice of assembled context — e.g. "Incident", "Timeline", "Risk Assessment".

    `content` is a deterministic, human-readable rendering ready to drop straight into a
    prompt. `data` is the same information kept structured, for consumers that want the
    underlying facts without re-parsing text (a future UI panel, a re-ranker, a RAG merge with
    retrieved document chunks)."""

    title: str
    content: str
    data: dict


class AIContext(BaseModel):
    """The Context Builder's single output shape, for every scope. This is the one place the
    AI layer assembles structured operational data before it reaches a prompt template or an
    AIProvider — nothing downstream re-queries the database."""

    scope: AIContextScope
    entity_id: UUID
    generated_at: datetime
    sections: list[ContextSection]

    def as_prompt_text(self) -> str:
        """Flattened, ordered text block ready for a prompt template's `{context}` placeholder."""
        return "\n\n".join(f"## {section.title}\n{section.content}" for section in self.sections)
