"""
Compound Risk Engine (CRE) — a deterministic, fully-explainable weighted rule engine that
combines zone-level operational signals (sensors, workers, equipment, permits, maintenance
state) into a structured risk assessment. Not ML/AI/fuzzy logic: every point of score traces
to a specific, independently-testable rule.

ENGINE_VERSION is stamped onto every RiskAssessment/RiskSnapshot so a future ML-assisted or
retuned engine can be compared against this one's historical output unambiguously.
"""

ENGINE_VERSION = "CRE-v1.0.0"
