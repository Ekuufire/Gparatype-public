"""Conservative deterministic calling rules for Gparatype v0.1."""

from __future__ import annotations

from gparatype.models import BlastHit, CallResult, TargetEvidence, TargetRecord

SPECIAL_5_12_NOTE = (
    "Howell molecular serotyping does not independently resolve serovars 5 vs 12 "
    "(shared wcwK target). Gparatype v0.1 reports SEROVAR_5_OR_12 and does not "
    "force a numbered 5 or 12 call."
)


def classify_hit(
    hit: BlastHit | None,
    *,
    min_identity: float,
    min_coverage: float,
) -> str:
    """Return PASS, PARTIAL, or ABSENT."""
    if hit is None:
        return "ABSENT"
    if hit.percent_identity >= min_identity and hit.query_coverage >= min_coverage:
        return "PASS"
    # Meaningful but below threshold
    if hit.alignment_length > 0 and hit.percent_identity > 0:
        return "PARTIAL"
    return "ABSENT"


def best_hit_for_query(hits: list[BlastHit], query_id: str) -> BlastHit | None:
    candidates = [h for h in hits if h.query_id == query_id]
    if not candidates:
        return None
    # Prefer higher bitscore, then identity, then coverage
    return max(
        candidates,
        key=lambda h: (h.bitscore, h.percent_identity, h.query_coverage, h.alignment_length),
    )


def build_evidence(
    targets: list[TargetRecord],
    hits: list[BlastHit],
    *,
    min_identity: float,
    min_coverage: float,
) -> list[TargetEvidence]:
    evidence: list[TargetEvidence] = []
    for t in targets:
        hit = best_hit_for_query(hits, t.query_id)
        status = classify_hit(hit, min_identity=min_identity, min_coverage=min_coverage)
        if hit is None:
            evidence.append(
                TargetEvidence(
                    serovar=t.serovar,
                    target_gene=t.gene,
                    target_accession=t.accession,
                    reference_strain=t.reference_strain,
                    query_id=t.query_id,
                    hit_status=status,
                    query_length=t.sequence_length,
                )
            )
        else:
            evidence.append(
                TargetEvidence(
                    serovar=t.serovar,
                    target_gene=t.gene,
                    target_accession=t.accession,
                    reference_strain=t.reference_strain,
                    query_id=t.query_id,
                    hit_status=status,
                    percent_identity=hit.percent_identity,
                    query_coverage=hit.query_coverage,
                    alignment_length=hit.alignment_length,
                    query_length=hit.query_length,
                    mismatches=hit.mismatches,
                    gaps=hit.gaps,
                    evalue=hit.evalue,
                    bitscore=hit.bitscore,
                    contig=hit.subject_id,
                    subject_start=hit.subject_start,
                    subject_end=hit.subject_end,
                    strand=hit.strand,
                )
            )
    return evidence


def _evidence_pass_status(e: TargetEvidence) -> str:
    """Prefer Phase 3C.1 final status when populated; else whole-CDS hit_status."""
    if e.final_serovar_evidence_status:
        return e.final_serovar_evidence_status
    return e.hit_status


def make_call(evidence: list[TargetEvidence]) -> CallResult:
    """Apply Rules A–D using validated per-serovar evidence statuses."""
    passing = [e for e in evidence if _evidence_pass_status(e) == "PASS"]
    partial = [e for e in evidence if _evidence_pass_status(e) == "PARTIAL"]
    # Diagnostic FAIL with whole-CDS presence is insufficient, not a final PASS
    insufficient_flags = [
        e
        for e in evidence
        if _evidence_pass_status(e) == "FAIL"
        or (
            e.evidence_mode == "PRIMER_PATTERN"
            and e.whole_cds_status == "PASS"
            and _evidence_pass_status(e) != "PASS"
        )
    ]
    pass_serovars = sorted({e.serovar for e in passing})

    five_twelve = [s for s in pass_serovars if s in (5, 12)]
    other = [s for s in pass_serovars if s not in (5, 12)]

    warnings: list[str] = []
    for e in evidence:
        if e.evidence_mode == "PRIMER_PATTERN" and e.whole_cds_status == "PASS" and _evidence_pass_status(e) != "PASS":
            warnings.append(
                f"Serovar {e.serovar}: whole-CDS {e.target_gene} homolog observed but diagnostic "
                f"primer-pair evidence failed (primer_pair_status={e.primer_pair_status})."
            )

    # Rule B — any 5/12 PASS (alone or with only 5/12)
    if five_twelve and not other:
        return CallResult(
            result_state="SEROVAR_5_OR_12",
            called_serovar=None,
            passing_serovars=pass_serovars,
            special_case_note=SPECIAL_5_12_NOTE,
            warnings=warnings,
        )

    # 5/12 plus unrelated targets → multiple
    if five_twelve and other:
        return CallResult(
            result_state="MULTIPLE_SEROVAR_TARGETS",
            called_serovar=None,
            passing_serovars=pass_serovars,
            special_case_note=SPECIAL_5_12_NOTE,
            warnings=warnings
            + ["Passing targets include both 5/12 wcwK and unrelated serovar targets."],
        )

    # Rule C — multiple non-5/12
    if len(other) > 1:
        return CallResult(
            result_state="MULTIPLE_SEROVAR_TARGETS",
            called_serovar=None,
            passing_serovars=pass_serovars,
            warnings=warnings,
        )

    # Rule A — exactly one clear non-5/12
    if len(other) == 1:
        return CallResult(
            result_state="SEROVAR_CALL",
            called_serovar=other[0],
            passing_serovars=pass_serovars,
            warnings=warnings,
        )

    # Rule D — nothing passes
    if partial or insufficient_flags:
        return CallResult(
            result_state="INSUFFICIENT_TARGET_MATCH",
            called_serovar=None,
            passing_serovars=[],
            warnings=warnings
            or ["Partial/failed diagnostic evidence present but no validated serovar PASS."],
        )
    return CallResult(
        result_state="NO_SEROVAR_TARGET",
        called_serovar=None,
        passing_serovars=[],
        warnings=warnings,
    )


def console_summary(call: CallResult) -> str:
    if call.result_state == "SEROVAR_CALL" and call.called_serovar is not None:
        return f"Gparatype result: Serovar {call.called_serovar}"
    if call.result_state == "SEROVAR_5_OR_12":
        return "Gparatype result: Serovar 5/12"
    if call.result_state == "MULTIPLE_SEROVAR_TARGETS":
        return "Gparatype result: Multiple serovar targets detected"
    if call.result_state == "NO_SEROVAR_TARGET":
        return "Gparatype result: No serovar target detected"
    if call.result_state == "INSUFFICIENT_TARGET_MATCH":
        return "Gparatype result: Insufficient target match"
    if call.result_state == "ERROR":
        return f"Gparatype result: ERROR ({call.error_message or 'see report'})"
    return f"Gparatype result: {call.result_state}"
