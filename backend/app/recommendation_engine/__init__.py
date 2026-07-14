"""
Compound Risk Engine -> Recommendation Engine. Deterministic, explainable, v1: a plain
rule_id -> template mapping (see templates.py), not a second reasoning engine — every risk
rule already encodes the domain knowledge needed to know what an operator should do about it.

ENGINE_VERSION is stamped on every persisted Recommendation, mirroring risk_engine's own
ENGINE_VERSION convention, so a future v2 (e.g. a real Recommendation Rule Engine, or an
LLM-assisted generator) can be compared against this one's historical output.
"""

ENGINE_VERSION = "REC-v1.0.0"
