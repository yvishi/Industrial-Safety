from datetime import datetime, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.config import AISettings
from app.ai.context.builder import ContextBuilder
from app.ai.exceptions import AIProviderNotConfiguredError, AITemplateNotFoundError
from app.ai.prompts.templates import ANALYTICS_QA, INCIDENT_EXPLANATION, get_template
from app.ai.providers.base import AIGenerationResult, AIProvider
from app.ai.providers.factory import build_ai_provider
from app.ai.providers.gemini import GeminiProvider
from app.ai.service import AIService
from app.core.exceptions import NotFoundError
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.zone import ZoneRepository


async def _create_plant_and_zone(client: AsyncClient) -> tuple[str, str]:
    plant = (await client.post("/api/v1/plants", json={"code": "TST-01", "name": "Test Plant"})).json()
    zone = (
        await client.post(
            "/api/v1/zones",
            json={
                "plant_id": plant["id"],
                "code": "ZN-01",
                "name": "Crude Distillation Unit",
                "zone_type": "crude_distillation",
            },
        )
    ).json()
    return plant["id"], zone["id"]


async def _create_incident(db_session: AsyncSession, *, zone_id: str) -> str:
    now = datetime(2026, 1, 1, 10, tzinfo=timezone.utc)
    incident = await IncidentRepository(db_session).create(
        {
            "primary_zone_id": UUID(zone_id),
            "affected_zone_ids": [zone_id],
            "status": "resolved",
            "origin": "system_detected",
            "classification": "safety_incident",
            "risk_severity_at_open": "high",
            "peak_risk_severity": "critical",
            "title": "H2S elevated in Crude Distillation Unit",
            "summary": "H2S concentration crossed into the critical band.",
            "opened_context_snapshot": {
                "sensors_outside_normal": [
                    {
                        "sensor_id": str(UUID(int=1)),
                        "tag_number": "H2S-1",
                        "sensor_type": "h2s",
                        "last_value": 42.0,
                        "effective_band": "critical",
                    }
                ],
                "workers_present": [],
                "active_permits": [],
                "equipment_not_operational": [],
                "categories": [],
                "contributors": [{"rule_id": "RULE_H2S_CRITICAL", "rationale": "H2S at critical threshold"}],
            },
            "opened_at": now,
            "resolved_at": now.replace(hour=11),
            "closed_at": None,
            "root_cause": "Seal failure on pump P-101",
            "corrective_actions": ["Replace seal", "Re-inspect pump"],
        }
    )
    return str(incident.id)


@pytest.fixture
def context_builder(db_session: AsyncSession) -> ContextBuilder:
    return ContextBuilder(
        IncidentRepository(db_session),
        EventRepository(db_session),
        RecommendationRepository(db_session),
        ZoneRepository(db_session),
    )


# --- Context Builder ---


async def test_build_incident_context_assembles_all_sections(
    client: AsyncClient, db_session: AsyncSession, context_builder: ContextBuilder
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    incident_id = await _create_incident(db_session, zone_id=zone_id)

    context = await context_builder.build_incident_context(UUID(incident_id))

    assert context.scope == "incident"
    assert str(context.entity_id) == incident_id
    titles = [section.title for section in context.sections]
    assert titles == ["Incident", "Timeline", "Risk Assessment", "Recommendations", "Resolution"]

    incident_section = context.sections[0]
    assert "H2S elevated" in incident_section.content
    assert incident_section.data["zone_name"] == "Crude Distillation Unit"

    risk_section = context.sections[2]
    assert "H2S at critical threshold" in risk_section.content
    assert "H2S-1" in risk_section.content

    resolution_section = context.sections[4]
    assert "Seal failure on pump P-101" in resolution_section.content
    assert resolution_section.data["resolved"] is True

    # The flattened prompt text carries every section, ordered, under a "## Title" heading.
    prompt_text = context.as_prompt_text()
    assert "## Incident" in prompt_text
    assert "## Resolution" in prompt_text


async def test_build_incident_context_missing_incident_raises_not_found(
    context_builder: ContextBuilder,
) -> None:
    with pytest.raises(NotFoundError):
        await context_builder.build_incident_context(UUID(int=999))


async def test_context_api_endpoint_returns_assembled_context(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    incident_id = await _create_incident(db_session, zone_id=zone_id)

    response = await client.get(f"/api/v1/ai/context/incidents/{incident_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "incident"
    assert len(body["sections"]) == 5


async def test_context_api_endpoint_404s_for_unknown_incident(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/ai/context/incidents/{UUID(int=999)}")
    assert response.status_code == 404


# --- Prompt templates ---


def test_prompt_template_renders_context_placeholder() -> None:
    rendered = INCIDENT_EXPLANATION.render(context="## Incident\nSomething happened.")
    assert "Something happened." in rendered
    assert INCIDENT_EXPLANATION.system_prompt


def test_prompt_template_renders_question_and_context() -> None:
    rendered = ANALYTICS_QA.render(question="Is the plant getting safer?", context="## Safety Trend\n...")
    assert "Is the plant getting safer?" in rendered
    assert "## Safety Trend" in rendered


def test_get_template_unknown_id_raises() -> None:
    with pytest.raises(AITemplateNotFoundError):
        get_template("does_not_exist")


# --- Provider abstraction ---


def test_gemini_provider_not_configured_without_api_key() -> None:
    settings = AISettings(gemini_api_key=None)
    provider = GeminiProvider(settings)
    assert provider.is_configured is False


async def test_gemini_provider_generate_raises_when_not_configured() -> None:
    provider = GeminiProvider(AISettings(gemini_api_key=None))
    with pytest.raises(AIProviderNotConfiguredError):
        await provider.generate(prompt="hello")


def test_build_ai_provider_returns_gemini_for_default_settings() -> None:
    provider = build_ai_provider(AISettings())
    assert isinstance(provider, GeminiProvider)


def test_build_ai_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        build_ai_provider(AISettings(provider="not-a-real-provider"))


# --- AIService orchestration (fake provider — no network) ---


class _FakeProvider(AIProvider):
    def __init__(self) -> None:
        self.last_prompt: str | None = None
        self.last_system_prompt: str | None = None

    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> AIGenerationResult:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return AIGenerationResult(text="fake response", model="fake-model", provider="fake")


async def test_ai_service_renders_template_and_calls_provider(
    client: AsyncClient, db_session: AsyncSession, context_builder: ContextBuilder
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    incident_id = await _create_incident(db_session, zone_id=zone_id)
    context = await context_builder.build_incident_context(UUID(incident_id))

    fake_provider = _FakeProvider()
    service = AIService(fake_provider)

    result = await service.generate(template_id="incident_explanation", context=context)

    assert result.text == "fake response"
    assert fake_provider.last_system_prompt == INCIDENT_EXPLANATION.system_prompt
    assert "## Incident" in (fake_provider.last_prompt or "")


async def test_ai_service_unknown_template_raises() -> None:
    service = AIService(_FakeProvider())
    with pytest.raises(AITemplateNotFoundError):
        await service.generate(template_id="does_not_exist")


# --- API health endpoint ---


async def test_ai_health_reports_unconfigured_by_default(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai/health")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "gemini"
    assert body["configured"] is False
