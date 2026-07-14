"""
Pure candidate generation: RiskAssessment -> list[RecommendationCandidate]. No I/O, no
database access, and deliberately does not read anything beyond RiskAssessment.contributors —
this is the architectural boundary agreed for the Recommendation Engine (it reasons over what
the Risk Engine already found, never raw sensor/worker/equipment facts directly).

This module is the entire "generation" half of the engine and is the seam a v2 Recommendation
Rule Engine would replace; everything downstream (persistence, lifecycle, API) depends only on
the RecommendationCandidate shape returned here, not on how it was produced.
"""

from collections import defaultdict
from dataclasses import dataclass

from app.recommendation_engine.templates import TEMPLATES, RecommendationTemplate, RULE_TEMPLATE_MAP
from app.risk_engine.config.schema import RiskCategory
from app.schemas.risk import EntityRefRead, RiskAssessment, RiskContributor

_SEVERITY_RANK: dict[str, int] = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


@dataclass(frozen=True)
class RecommendationCandidate:
    template_id: str
    category: RiskCategory
    title: str
    action_text: str
    expected_outcomes: tuple[str, ...]
    priority: str  # critical|high|moderate|low
    rationale: str
    source_rule_ids: tuple[str, ...]
    target_entity: EntityRefRead


def generate_candidates(assessment: RiskAssessment) -> list[RecommendationCandidate]:
    """One candidate per template currently represented among the assessment's triggered
    contributors — contributors that map to the same template (because their rules already
    carry the same operator guidance) are merged into a single candidate rather than shown as
    near-duplicate cards."""
    groups: dict[str, list[RiskContributor]] = defaultdict(list)
    for contributor in assessment.contributors:
        template_id = RULE_TEMPLATE_MAP.get(contributor.rule_id)
        if template_id is not None:
            groups[template_id].append(contributor)

    zone_ref = EntityRefRead(entity_type="zone", entity_id=assessment.zone_id, label=assessment.zone_name)

    candidates = [
        _build_candidate(TEMPLATES[template_id], contributors, assessment, zone_ref)
        for template_id, contributors in groups.items()
    ]
    candidates.sort(key=lambda c: (_SEVERITY_RANK.get(c.priority, 9), -_total_impact(c, groups)))
    return candidates


def _build_candidate(
    template: RecommendationTemplate,
    contributors: list[RiskContributor],
    assessment: RiskAssessment,
    zone_ref: EntityRefRead,
) -> RecommendationCandidate:
    primary = min(contributors, key=lambda c: _SEVERITY_RANK.get(c.severity, 9))
    priority = "critical" if assessment.is_emergency_override else primary.severity
    return RecommendationCandidate(
        template_id=template.template_id,
        category=template.category,
        title=template.title,
        action_text=template.action_text,
        expected_outcomes=template.expected_outcomes,
        priority=priority,
        rationale=primary.rationale,
        source_rule_ids=tuple(sorted(c.rule_id for c in contributors)),
        target_entity=_resolve_target(template, contributors, zone_ref),
    )


def _resolve_target(
    template: RecommendationTemplate, contributors: list[RiskContributor], zone_ref: EntityRefRead
) -> EntityRefRead:
    if template.target_entity_type != "zone":
        for contributor in contributors:
            for ref in contributor.source_refs:
                if ref.entity_type == template.target_entity_type:
                    return ref
    return zone_ref


def _total_impact(candidate: RecommendationCandidate, groups: dict[str, list[RiskContributor]]) -> int:
    return sum(c.impact for c in groups[candidate.template_id])
