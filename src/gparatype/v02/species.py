"""Conservative DEVELOPMENT species proxy using Howell CDS homology.

Limitation: this is NOT a clinically validated species assay. It uses capsule
CDS homology as a rough proxy that capsule-associated Glaesserella/Haemophilus
parasuis-like sequence is present.
"""

from __future__ import annotations

from gparatype.v02.constants import (
    DEVELOPMENT_DEFAULT_SPECIES_OK_MIN,
    DEVELOPMENT_DEFAULT_SPECIES_WEAK_MIN,
)
from gparatype.v02.models import ComponentHit


def assess_species(
    search_hits: list[ComponentHit],
    *,
    ok_min: int = DEVELOPMENT_DEFAULT_SPECIES_OK_MIN,
    weak_min: int = DEVELOPMENT_DEFAULT_SPECIES_WEAK_MIN,
) -> tuple[str, int, list[str]]:
    """Return (status, unique_accession_count, warnings).

    SPECIES_OK if unique accessions >= ok_min
    SPECIES_WEAK if weak_min <= count < ok_min (warn, may continue)
    SPECIES_CHECK_FAILED if count < weak_min
    """
    accessions = {h.accession for h in search_hits if h.accession}
    n = len(accessions)
    warnings: list[str] = [
        "Species check uses Howell capsule CDS homology as a DEVELOPMENT proxy only; "
        "not a clinically validated species assay."
    ]
    if n >= ok_min:
        return "SPECIES_OK", n, warnings
    if n >= weak_min:
        warnings.append(
            f"SPECIES_WEAK: only {n} unique Howell CDS accessions with SEARCH-level hits "
            f"(DEVELOPMENT default ok_min={ok_min})."
        )
        return "SPECIES_WEAK", n, warnings
    warnings.append(
        f"SPECIES_CHECK_FAILED: {n} unique Howell CDS SEARCH hits (need >={weak_min})."
    )
    return "SPECIES_CHECK_FAILED", n, warnings
