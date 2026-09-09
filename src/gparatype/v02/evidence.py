"""Assemble per-serovar ArchitectureEvidenceProfile (qualitative evidence dims)."""

from __future__ import annotations

from gparatype.v02.constants import DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT
from gparatype.v02.database import GparatypeDatabase
from gparatype.v02.models import (
    ArchitectureEvidenceProfile,
    ArchitectureProfile,
    DiagnosticEvidence,
)


def _content_label(recovery: float, min_support: float) -> str:
    if recovery >= max(0.75, min_support + 0.2):
        return "STRONG"
    if recovery >= min_support:
        return "MODERATE"
    if recovery >= 0.25:
        return "WEAK"
    if recovery > 0:
        return "INDETERMINATE"
    return "NOT_ASSESSABLE"


def _sequence_label(arch: ArchitectureProfile) -> str:
    scored = [
        c
        for c in arch.components
        if c.status in ("PRESENT", "PARTIAL") and c.percent_identity is not None
    ]
    if not scored:
        return "NOT_ASSESSABLE"
    mean_p = sum(c.percent_identity or 0 for c in scored) / len(scored)
    if mean_p >= 95:
        return "STRONG"
    if mean_p >= 85:
        return "MODERATE"
    if mean_p >= 70:
        return "WEAK"
    return "INDETERMINATE"


def _map_order(status: str) -> str:
    if status == "ORDER_AGREE":
        return "STRONG"
    if status == "ORDER_DISAGREE":
        return "WEAK"
    return "NOT_ASSESSABLE"


def _map_adj(status: str) -> str:
    if status == "ADJACENCY_AGREE":
        return "STRONG"
    if status == "ADJACENCY_DISAGREE":
        return "WEAK"
    return "NOT_ASSESSABLE"


def _map_ori(status: str) -> str:
    if status == "ORIENTATION_AGREE":
        return "MODERATE"
    if status == "ORIENTATION_DISAGREE":
        return "WEAK"
    return "NOT_ASSESSABLE"


def _map_diag(status: str) -> str:
    return {
        "STRONG": "STRONG",
        "MODERATE": "MODERATE",
        "WEAK": "WEAK",
        "DIVERGENT": "INDETERMINATE",
        "ABSENT": "NOT_ASSESSABLE",
        "NOT_ASSESSABLE": "NOT_ASSESSABLE",
    }.get(status, "NOT_ASSESSABLE")


def _completeness_label(arch: ArchitectureProfile) -> str:
    if arch.n_expected == 0:
        return "NOT_ASSESSABLE"
    obs_frac = arch.n_not_observable / arch.n_expected
    if arch.recovery_fraction >= 0.75 and obs_frac < 0.25:
        return "STRONG"
    if arch.recovery_fraction >= 0.5:
        return "MODERATE"
    if arch.n_not_observable > arch.n_not_detected and arch.recovery_fraction >= 0.25:
        return "INDETERMINATE"
    if arch.recovery_fraction > 0:
        return "WEAK"
    return "NOT_ASSESSABLE"


def assemble_evidence_profiles(
    db: GparatypeDatabase,
    architectures: list[ArchitectureProfile],
    diagnostics: dict[int, DiagnosticEvidence],
    *,
    min_content: float = DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT,
) -> list[ArchitectureEvidenceProfile]:
    # Rank recoveries to annotate competing_evidence later (filled in interpretation too)
    ranked = sorted(architectures, key=lambda a: a.recovery_fraction, reverse=True)
    top_rec = ranked[0].recovery_fraction if ranked else 0.0

    profiles: list[ArchitectureEvidenceProfile] = []
    for arch in architectures:
        s = arch.serovar
        mode = db.modes.get(s, {})
        sero = db.serovars.get(s)
        diag = diagnostics.get(s)
        warnings = list(arch.warnings)
        if s == 6:
            warnings.append(
                "Serovar 6: unresolved gltI assay-region questions; readiness provisional."
            )
        if sero and sero.readiness in ("PROVISIONAL", "INSUFFICIENT_DATA", "SPECIAL_CASE"):
            warnings.append(f"validation_readiness={sero.readiness}")

        competing = "NOT_ASSESSABLE"
        if top_rec > 0 and arch.recovery_fraction > 0:
            delta = top_rec - arch.recovery_fraction
            if arch.serovar == ranked[0].serovar:
                competing = "INDETERMINATE"  # self; refined later
            elif delta <= 0.15:
                competing = "STRONG"
            elif delta <= 0.30:
                competing = "MODERATE"
            else:
                competing = "WEAK"

        profiles.append(
            ArchitectureEvidenceProfile(
                serovar=s,
                reference_strain=arch.reference_strain,
                evidence_mode=mode.get("proposed_future_evidence_mode")
                or mode.get("evidence_mode")
                or (sero.evidence_mode if sero else ""),
                readiness=mode.get("current_readiness_for_v02")
                or (sero.readiness if sero else ""),
                content_evidence=_content_label(arch.recovery_fraction, min_content),
                sequence_evidence=_sequence_label(arch),
                order_evidence=_map_order(arch.order_status),
                adjacency_evidence=_map_adj(arch.adjacency_status),
                orientation_evidence=_map_ori(arch.orientation_status),
                diagnostic_evidence=_map_diag(diag.status if diag else "ABSENT"),
                completeness_evidence=_completeness_label(arch),
                assembly_limitations="STRONG" if arch.assembly_limited else "NOT_ASSESSABLE",
                competing_evidence=competing,
                recovery_fraction=arch.recovery_fraction,
                warnings=warnings,
                architecture=arch,
                diagnostic=diag,
            )
        )
    return profiles
