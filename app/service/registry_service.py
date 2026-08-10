"""
registry_service.py
-------------------
Resolves SHAP features against the salary-slip registry and builds
the enriched context block that is injected into the LLM user message.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.registry.salary_slips_registry import (
    SALARY_SLIP_FEATURE_REGISTRY,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _severity_label(contribution: float) -> str:
    """Map a SHAP contribution to a severity label for unregistered features."""
    if contribution >= 0.30:
        return "HIGH"
    elif contribution >= 0.10:
        return "MEDIUM"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ResolvedFeature:
    """A single SHAP feature resolved against the registry."""
    feature: str
    contribution: float
    severity: str
    title: str
    action: str
    instruction: str
    category: str


@dataclass
class RegistryContext:
    """
    Everything the CRUD layer needs to enrich the LLM user message.

    individual_findings  – features resolved 1-to-1 from the registry
    unknown_features     – qualifying features absent from the registry
                           (passed through as-is so the LLM falls back
                           to its own title-generation rules)
    """
    individual_findings: List[ResolvedFeature] = field(default_factory=list)
    unknown_features: List[dict] = field(default_factory=list)


def resolve(shap_features: list) -> RegistryContext:
    """
    Resolve a list of shap_feature objects (with .feature / .contribution)
    against the salary-slip registry.

    Only features with contribution >= 0.05 are considered (matching the
    prompt's evidence rules).  The caller may pass the full list; this
    function filters internally.

    Returns a :class:`RegistryContext` with:
    - individual_findings  (known features)
    - unknown_features     (feature keys not present in the registry)
    """
    # 1. Filter to qualifying SHAP entries
    qualifying = [sf for sf in shap_features if sf.contribution >= 0.05]

    if not qualifying:
        return RegistryContext()

    # 2. Resolve each feature against the registry
    resolved: List[ResolvedFeature] = []
    unknown: List[dict] = []

    for sf in qualifying:
        entry = SALARY_SLIP_FEATURE_REGISTRY.get(sf.feature)
        if entry is None:
            unknown.append({
                "feature": sf.feature,
                "contribution": sf.contribution,
                "severity": _severity_label(sf.contribution)
            })
            continue

        resolved.append(
            ResolvedFeature(
                feature=sf.feature,
                contribution=sf.contribution,
                severity=entry["severity"],
                title=entry["title"],
                action=entry["action"],
                instruction=entry["instruction"],
                category=entry["category"],
            )
        )

    return RegistryContext(
        individual_findings=resolved,
        unknown_features=unknown,
    )


def build_registry_context_block(ctx: RegistryContext) -> str:
    """
    Render the RegistryContext into a plain-text block that is appended
    to the LLM user message under the heading ``REGISTRY CONTEXT``.

    The LLM's system prompt instructs it to use this information
    exactly as provided when generating each finding.
    """
    if not ctx.individual_findings and not ctx.unknown_features:
        return ""

    lines: List[str] = ["", "REGISTRY CONTEXT", ""]

    # --- Individual findings ------------------------------------------------
    for rf in ctx.individual_findings:
        lines.append(f"Feature: {rf.feature}")
        lines.append(f"  Severity: {rf.severity}")
        lines.append(f"  Title: {rf.title}")
        lines.append(f"  Category: {rf.category}")
        lines.append(f"  Recommended action: {rf.action}")
        lines.append(f"  Writing instruction: {rf.instruction}")
        lines.append("")

    # --- Unknown features (pass-through note) --------------------------------
    if ctx.unknown_features:
        lines.append("Unregistered features (use prompt fallback rules for title/explanation):")
        for u in ctx.unknown_features:
            lines.append(f"  - {u['feature']} (Severity: {u['severity']})")
        lines.append("")

    return "\n".join(lines)
