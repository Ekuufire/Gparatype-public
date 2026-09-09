"""Capsule-associated sequence locator summary."""

from __future__ import annotations

from gparatype.v02.constants import (
    DEVELOPMENT_DEFAULT_PARTIAL_PIDENT,
    DEVELOPMENT_DEFAULT_PARTIAL_QCOV,
    DEVELOPMENT_DEFAULT_PRESENT_PIDENT,
    DEVELOPMENT_DEFAULT_PRESENT_QCOV,
)
from gparatype.v02.models import ComponentHit


def label_hit_presence(hit: ComponentHit) -> str:
    """Label a single hit PRESENT / PARTIAL / WEAK using DEVELOPMENT defaults."""
    if (
        hit.percent_identity >= DEVELOPMENT_DEFAULT_PRESENT_PIDENT
        and hit.query_coverage >= DEVELOPMENT_DEFAULT_PRESENT_QCOV
    ):
        return "PRESENT"
    if (
        hit.percent_identity >= DEVELOPMENT_DEFAULT_PARTIAL_PIDENT
        and hit.query_coverage >= DEVELOPMENT_DEFAULT_PARTIAL_QCOV
    ):
        return "PARTIAL"
    return "WEAK"


def locate_capsule(search_hits: list[ComponentHit]) -> dict:
    """Summarize whether capsule-associated sequence was detected."""
    present = 0
    partial = 0
    for h in search_hits:
        lab = label_hit_presence(h)
        if lab == "PRESENT":
            present += 1
        elif lab == "PARTIAL":
            partial += 1
    detected = (present + partial) > 0
    return {
        "capsule_detected": detected,
        "n_present_like": present,
        "n_partial_like": partial,
        "n_search_hits": len(search_hits),
    }
