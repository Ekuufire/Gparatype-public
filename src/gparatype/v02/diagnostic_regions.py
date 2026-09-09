"""Diagnostic region evidence (Howell 2015 targets) — descriptive labels only."""

from __future__ import annotations

from gparatype.v02.constants import (
    DEVELOPMENT_DEFAULT_DIAG_MODERATE_PIDENT,
    DEVELOPMENT_DEFAULT_DIAG_MODERATE_QCOV,
    DEVELOPMENT_DEFAULT_DIAG_STRONG_PIDENT,
    DEVELOPMENT_DEFAULT_DIAG_STRONG_QCOV,
    DEVELOPMENT_DEFAULT_DIAG_WEAK_PIDENT,
    DEVELOPMENT_DEFAULT_DIAG_WEAK_QCOV,
)
from gparatype.v02.database import GparatypeDatabase
from gparatype.v02.models import ComponentHit, DiagnosticEvidence


def _label_diagnostic(pident: float | None, qcov: float | None) -> str:
    if pident is None or qcov is None:
        return "ABSENT"
    if pident >= DEVELOPMENT_DEFAULT_DIAG_STRONG_PIDENT and qcov >= DEVELOPMENT_DEFAULT_DIAG_STRONG_QCOV:
        return "STRONG"
    if pident >= DEVELOPMENT_DEFAULT_DIAG_MODERATE_PIDENT and qcov >= DEVELOPMENT_DEFAULT_DIAG_MODERATE_QCOV:
        return "MODERATE"
    if pident >= DEVELOPMENT_DEFAULT_DIAG_WEAK_PIDENT and qcov >= DEVELOPMENT_DEFAULT_DIAG_WEAK_QCOV:
        return "WEAK"
    if pident >= DEVELOPMENT_DEFAULT_DIAG_WEAK_PIDENT:
        return "DIVERGENT"
    return "ABSENT"


def assess_diagnostic_regions(
    db: GparatypeDatabase,
    search_hits: list[ComponentHit],
) -> dict[int, DiagnosticEvidence]:
    by_acc = {h.accession: h for h in search_hits}
    out: dict[int, DiagnosticEvidence] = {}
    for serovar, tgt in db.diagnostic_targets.items():
        hit = by_acc.get(tgt.accession)
        if hit is None:
            out[serovar] = DiagnosticEvidence(
                serovar=serovar,
                gene=tgt.gene,
                accession=tgt.accession,
                status="ABSENT",
            )
        else:
            out[serovar] = DiagnosticEvidence(
                serovar=serovar,
                gene=tgt.gene,
                accession=tgt.accession,
                status=_label_diagnostic(hit.percent_identity, hit.query_coverage),
                percent_identity=hit.percent_identity,
                query_coverage=hit.query_coverage,
                contig=hit.contig,
            )
    return out
