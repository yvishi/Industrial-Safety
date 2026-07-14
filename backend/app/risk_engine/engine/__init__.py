"""Risk Engine scoring layer: aggregation, confidence, trend, and explanation generation.

Consumes the RuleResult list produced by app/risk_engine/rules and turns it into the scored,
explained shape the API layer serializes. No Pydantic here — these are internal engine shapes,
converted to API schemas by a different layer.
"""
