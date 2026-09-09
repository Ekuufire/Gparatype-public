"""Phase 5E hybrid interpretation — architecture-aware conservative calling.

Implements frozen Phase 5D.1 candidate calling rules exactly.
SOFTWARE research prototype only. Prefer AMBIGUOUS / ASSEMBLY_LIMITED over
unsupported numbered calls. Never hardcode challenge-isolate strain identifiers
into calling logic.
"""

from __future__ import annotations

from gparatype.v02.constants import (
    DEVELOPMENT_DEFAULT_COMPETING_DELTA,
    DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT,
)
from gparatype.v02.models import (
    ArchitectureEvidenceProfile,
    ComponentStatus,
    InterpretationResult,
)

# Evidence-mode labels from Phase 5D.1 (documentation crosswalk only)
HYBRID_REQUIRED = frozenset({1, 4, 7, 11, 14, 15})
DIAGNOSTIC_REGION_DOMINANT = frozenset({3, 9, 13})
ARCHITECTURE_DOMINANT = frozenset({6})
MORE_BIOLOGY = frozenset({2, 8, 10})
SPECIAL_CASE_5_12 = frozenset({5, 12})

FAMILY_1_2_7_11 = frozenset({1, 2, 7, 11})
FAMILY_4_14_15 = frozenset({4, 14, 15})
FAMILY_8_10 = frozenset({8, 10})

# Primary diagnostic gene anchors (Howell 2015 / Phase 5D.1)
DIAG_GENE = {
    1: "funB",
    2: "wzx",
    3: "glyC",
    4: "wciP",
    5: "wcwK",
    6: "gltI",
    7: "funQ",
    8: "scdA",
    9: "funV",
    10: "funX",
    11: "amtA",
    12: "wcwK",
    13: "gltP",
    14: "funAB",
    15: "funI",
}

# Flanking / neighborhood genes used for locus-context checks (Phase 5D.1)
FLANKS = {
    1: ("funA", "hydA", "gptA", "wbuS"),
    2: ("funA", "funE"),
    4: ("neuA", "wzx", "mepA", "gltF", "gltG", "lstB", "lstA", "funA"),
    6: ("lsgB", "gltH", "funL", "wcfQ"),
    7: ("funP", "astA", "gltJ", "neuA", "wzx"),
    8: ("astA", "gltH", "adlA", "funS", "gltK"),
    10: ("astA", "gltH", "adlA", "funS", "gltK"),
    11: ("funY", "actA", "bstA", "gltO", "capD", "funB", "hydA"),
    14: ("funAA", "funAC", "wzxB", "gstA", "gltQ", "uaeA"),
    15: ("funJ", "gltR", "gltE", "neuA", "wzx"),
}


def _metadata_agreement(reported: str | None, primary: str) -> str:
    if not reported or not str(reported).strip():
        return "NOT_SUPPLIED"
    rep = str(reported).strip().upper().replace("SEROVAR", "").replace(" ", "")
    prim = primary.strip().upper()
    if prim in ("5_OR_12", "5OR12") and rep in ("5", "12", "5_OR_12", "5OR12", "5/12"):
        return "AGREE"
    if rep == prim or rep == prim.replace("_OR_", "/"):
        return "AGREE"
    return "DISCORDANT_METADATA"


def _diag_rank(label: str) -> int:
    return {
        "STRONG": 4,
        "MODERATE": 3,
        "WEAK": 2,
        "DIVERGENT": 1,
        "INDETERMINATE": 1,
        "ABSENT": 0,
        "NOT_ASSESSABLE": 0,
    }.get((label or "").upper(), 0)


def _diag_supportive(p: ArchitectureEvidenceProfile) -> bool:
    return p.diagnostic_evidence in ("STRONG", "MODERATE")


def _diag_divergent(p: ArchitectureEvidenceProfile) -> bool:
    return p.diagnostic_evidence in ("DIVERGENT", "WEAK")


def _architecture_supportive(p: ArchitectureEvidenceProfile) -> bool:
    return (
        p.content_evidence in ("STRONG", "MODERATE")
        and p.recovery_fraction >= DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT
    )


def _order_or_adj_ok(p: ArchitectureEvidenceProfile) -> bool:
    return p.order_evidence in ("STRONG", "MODERATE") or p.adjacency_evidence in (
        "STRONG",
        "MODERATE",
    )


def _norm_gene(name: str) -> str:
    return (name or "").strip().lower().replace("-", "").replace("_", "")


def _components(p: ArchitectureEvidenceProfile) -> list[ComponentStatus]:
    if not p.architecture:
        return []
    return list(p.architecture.components or [])


def _gene_hits(p: ArchitectureEvidenceProfile, *gene_names: str) -> list[ComponentStatus]:
    want = {_norm_gene(g) for g in gene_names}
    hits: list[ComponentStatus] = []
    for c in _components(p):
        g = _norm_gene(c.gene)
        # Exact or prefix match (funAB vs funA handled carefully: require token match)
        if g in want or any(g == w or g.startswith(w) or w.startswith(g) for w in want):
            if c.status in ("PRESENT", "PARTIAL"):
                hits.append(c)
    return hits


def _gene_present(p: ArchitectureEvidenceProfile, *gene_names: str) -> bool:
    return bool(_gene_hits(p, *gene_names))


def _anchor_with_flank_same_contig(
    p: ArchitectureEvidenceProfile,
    anchor: str,
    flanks: tuple[str, ...],
) -> bool:
    """True when diagnostic anchor and ≥1 flank gene share a contig."""
    anchors = _gene_hits(p, anchor)
    if not anchors:
        # Fall back: diagnostic object contig + any flank on that contig
        diag = p.diagnostic
        if diag is None or not diag.contig or not _diag_supportive(p):
            return False
        for f in _gene_hits(p, *flanks):
            if f.contig and f.contig == diag.contig:
                return True
        return False
    for a in anchors:
        if not a.contig:
            continue
        for f in _gene_hits(p, *flanks):
            if f.contig and f.contig == a.contig:
                return True
    return False


def _locus_context_ok(p: ArchitectureEvidenceProfile, serovar: int) -> bool:
    """Minimum assessable locus context for hybrid/architecture rules."""
    gene = DIAG_GENE.get(serovar, "")
    flanks = FLANKS.get(serovar, ())
    if gene and flanks and _anchor_with_flank_same_contig(p, gene, flanks):
        return True
    # Order/adjacency evidence with architecture content counts as locus context
    if _architecture_supportive(p) and _order_or_adj_ok(p):
        return True
    # Multiple recovered components beyond a lone diagnostic gene
    comps = [c for c in _components(p) if c.status in ("PRESENT", "PARTIAL")]
    if gene:
        non_diag = [c for c in comps if _norm_gene(gene) not in _norm_gene(c.gene)]
        if len(non_diag) >= 2 and _architecture_supportive(p):
            return True
    return False


def _region2_ok(p: ArchitectureEvidenceProfile) -> bool:
    """Region-2 completeness proxy: supportive architecture without assembly dominance."""
    if not _architecture_supportive(p):
        return False
    if p.architecture and p.architecture.assembly_limited:
        n_exp = p.architecture.n_expected or 1
        if p.architecture.n_not_observable / n_exp >= 0.3 and p.recovery_fraction < 0.75:
            return False
    if p.completeness_evidence in ("WEAK", "INDETERMINATE", "NOT_ASSESSABLE"):
        if p.recovery_fraction < 0.60:
            return False
    return True


def _incomplete(p: ArchitectureEvidenceProfile) -> bool:
    if p.architecture and p.architecture.assembly_limited:
        return True
    if p.recovery_fraction < DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT:
        return True
    if p.content_evidence in ("WEAK", "INDETERMINATE", "NOT_ASSESSABLE"):
        return True
    if p.completeness_evidence in ("WEAK", "INDETERMINATE") and p.recovery_fraction < 0.60:
        return True
    return False


def _profile_by_sero(
    profiles: list[ArchitectureEvidenceProfile],
) -> dict[int, ArchitectureEvidenceProfile]:
    return {p.serovar: p for p in profiles}


def _dominant_competing_diagnostics(
    profiles: list[ArchitectureEvidenceProfile],
    family: frozenset[int],
    best: ArchitectureEvidenceProfile,
    competing_delta: float,
) -> list[int]:
    """Return family members with competing dominant diagnostic/architecture signals."""
    rivals: list[int] = []
    for p in profiles:
        if p.serovar not in family or p.serovar == best.serovar:
            continue
        close_arch = abs(best.recovery_fraction - p.recovery_fraction) <= competing_delta and (
            p.recovery_fraction >= 0.25
        )
        strong_diag = _diag_supportive(p) and _diag_rank(p.diagnostic_evidence) >= _diag_rank(
            best.diagnostic_evidence
        )
        if close_arch or (strong_diag and _architecture_supportive(p)):
            rivals.append(p.serovar)
        elif strong_diag and not _diag_supportive(best):
            rivals.append(p.serovar)
    return rivals


def _result(
    *,
    final_state: str,
    primary: str = "",
    interpretation: str,
    competing: list[str] | None = None,
    warnings: list[str],
    reported: str | None,
    species_status: str,
    details: dict | None = None,
) -> InterpretationResult:
    return InterpretationResult(
        final_state=final_state,
        primary_architecture_serovar=primary,
        interpretation=interpretation,
        competing_serovars=competing or [],
        warnings=warnings,
        metadata_agreement=_metadata_agreement(reported, primary),
        species_status=species_status,
        details=details or {"interpretation_mode": "hybrid"},
    )


def _evaluate_serovar_support(
    best: ArchitectureEvidenceProfile,
    by: dict[int, ArchitectureEvidenceProfile],
    warnings: list[str],
) -> tuple[bool, str | None, list[str]]:
    """Return (supported_ok, override_state, extra_warnings).

    override_state: if set, emit that state instead of SUPPORTED/AMBIGUOUS default.
    """
    s = best.serovar
    extra: list[str] = []

    # --- SPECIAL CASE 5/12 handled upstream ---
    if s in SPECIAL_CASE_5_12:
        return False, None, extra

    # --- Serovar 1: HYBRID — funB + locus-context; exclude dominant amtA/wzx/funQ ---
    if s == 1:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 1: funB diagnostic not supportive."]
        if not _locus_context_ok(best, 1):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 1: funB alone without locus-context → AMBIGUOUS (never funB alone)."
            ]
        for rival_s, rival_gene in ((11, "amtA"), (2, "wzx"), (7, "funQ")):
            rp = by.get(rival_s)
            if rp and _diag_supportive(rp) and (
                rp.recovery_fraction >= best.recovery_fraction - 0.05
                or _diag_rank(rp.diagnostic_evidence) > _diag_rank(best.diagnostic_evidence)
            ):
                return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                    f"Serovar 1: competing dominant {rival_gene} (serovar {rival_s}) → AMBIGUOUS."
                ]
        if not _architecture_supportive(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 1: supporting architecture insufficient."
            ]
        return True, None, extra

    # --- Serovar 2: MORE_BIOLOGY — never force ---
    if s == 2:
        if _incomplete(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 2: truncated/split/incomplete architecture → AMBIGUOUS (MORE_BIOLOGY)."
            ]
        wzx_ok = _diag_supportive(best) or (
            best.diagnostic is not None
            and best.diagnostic.percent_identity is not None
            and best.diagnostic.percent_identity >= 90.0
            and best.diagnostic.query_coverage is not None
            and best.diagnostic.query_coverage >= 70.0
        )
        if not wzx_ok:
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 2: wzx diagnostic/high-id amplicon not met."
            ]
        if not _anchor_with_flank_same_contig(best, "wzx", FLANKS[2]) and not (
            _gene_present(best, "funA") and _gene_present(best, "wzx") and _gene_present(best, "funE")
        ):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 2: require funA>wzx>funE / wzx+flank same contig."
            ]
        if not _architecture_supportive(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 2: architecture support insufficient; never force."
            ]
        return True, None, extra + ["Serovar 2: MORE_BIOLOGY_REQUIRED — conservative support only."]

    # --- Serovar 3: DIAGNOSTIC_REGION_DOMINANT (glyC) ---
    if s == 3:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 3: glyC diagnostic not supportive."]
        if _incomplete(best) and best.recovery_fraction < 0.35:
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 3: locus incompleteness → AMBIGUOUS."
            ]
        # Diagnostic-region dominant: hybrid architecture not required when diag qualifies
        return True, None, extra

    # --- Serovar 4: HYBRID — wciP + Region-2; exclude funAB/funI ---
    if s == 4:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 4: wciP diagnostic not supportive."]
        if not _region2_ok(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 4: Region-2 incompleteness → AMBIGUOUS."
            ]
        for rival_s, gene in ((14, "funAB"), (15, "funI")):
            rp = by.get(rival_s)
            if rp and _diag_supportive(rp):
                return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                    f"Serovar 4: exclude opposite diagnostic anchor {gene} → AMBIGUOUS."
                ]
        return True, None, extra

    # --- Serovar 6: ARCHITECTURE_DOMINANT (gltI neighborhood) ---
    if s == 6:
        extra.append(
            "Serovar 6: PCR_ASSAY_COMPATIBILITY imperfect (published reverse primer "
            "1-nt vs KC795372.1; primer unmodified). "
            "GENOMIC_SIGNATURE_COMPATIBILITY assessed via architecture/neighborhood."
        )
        neigh = _gene_present(best, "gltI") and (
            _gene_present(best, "lsgB", "gltH", "funL", "wcfQ")
            or _anchor_with_flank_same_contig(best, "gltI", FLANKS[6])
        )
        # Architecture may carry gltI neighborhood without exact primer pair
        if not neigh and not (
            _architecture_supportive(best)
            and (_gene_present(best, "funL") or _gene_present(best, "gltI") or _order_or_adj_ok(best))
        ):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 6: gltI neighborhood not established."
            ]
        # Exclude wcwK-dominant 5/12 without gltI/funL
        p5 = by.get(5)
        p12 = by.get(12)
        wcw_dom = False
        for px in (p5, p12):
            if px and px.recovery_fraction > best.recovery_fraction + 0.05 and _gene_present(px, "wcwK"):
                if not (_gene_present(best, "gltI") or _gene_present(best, "funL")):
                    wcw_dom = True
        if wcw_dom:
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 6: wcwK-dominant 5/12 core without gltI/funL."
            ]
        if not _architecture_supportive(best) and not neigh:
            return False, "AMBIGUOUS_ARCHITECTURE", extra
        return True, None, extra

    # --- Serovar 7: HYBRID — funQ + supporting architecture ---
    if s == 7:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 7: funQ diagnostic not supportive."]
        if not _architecture_supportive(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 7: supporting architecture insufficient."
            ]
        rivals = []
        for rival_s in (1, 2, 11):
            rp = by.get(rival_s)
            if rp and _diag_supportive(rp) and _architecture_supportive(rp):
                if abs(rp.recovery_fraction - best.recovery_fraction) <= 0.15:
                    rivals.append(rival_s)
        if rivals:
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                f"Serovar 7: family competition with {rivals} → AMBIGUOUS."
            ]
        return True, None, extra

    # --- Serovar 8: MORE_BIOLOGY — scdA + backbone; never force ---
    if s == 8:
        if _incomplete(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 8: incomplete evidence → AMBIGUOUS (MORE_BIOLOGY; never force)."
            ]
        if not _diag_supportive(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 8: scdA diagnostic not supportive."
            ]
        if not (
            _anchor_with_flank_same_contig(best, "scdA", FLANKS[8])
            or (_gene_present(best, "scdA") and _gene_present(best, "astA", "gltH", "adlA", "funS"))
        ):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 8: shared backbone alone insufficient; need scdA + neighbor."
            ]
        p10 = by.get(10)
        if p10 and _diag_supportive(p10) and not _diag_supportive(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 8: funX-dominant competitor without clear scdA → AMBIGUOUS."
            ]
        if p10 and _diag_supportive(p10) and _architecture_supportive(p10):
            if abs(p10.recovery_fraction - best.recovery_fraction) <= 0.15:
                return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                    "Serovar 8/10: shared backbone without clear scdA vs funX → AMBIGUOUS."
                ]
        return True, None, extra + ["Serovar 8: MORE_BIOLOGY_REQUIRED — conservative support only."]

    # --- Serovar 9: DIAGNOSTIC_REGION_DOMINANT (funV) ---
    if s == 9:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 9: funV diagnostic not supportive."]
        if _incomplete(best) and best.recovery_fraction < 0.35:
            return False, "AMBIGUOUS_ARCHITECTURE", extra
        return True, None, extra

    # --- Serovar 10: MORE_BIOLOGY — funX + backbone; divergent → AMBIGUOUS ---
    if s == 10:
        if _incomplete(best) or _diag_divergent(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 10: divergent/incomplete funX evidence → AMBIGUOUS "
                "(MORE_BIOLOGY; never force; ~83% divergent subset recognized as unresolved)."
            ]
        if not _diag_supportive(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 10: funX diagnostic not supportive."
            ]
        # Explicit ~83% divergent recognition via diagnostic identity when available
        if (
            best.diagnostic is not None
            and best.diagnostic.percent_identity is not None
            and best.diagnostic.percent_identity < 90.0
        ):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 10: funX identity below high-id band (~83% divergent subset) → AMBIGUOUS."
            ]
        if not (
            _anchor_with_flank_same_contig(best, "funX", FLANKS[10])
            or (_gene_present(best, "funX") and _gene_present(best, "astA", "gltH", "adlA", "funS"))
        ):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 10: need funX + backbone neighbor."
            ]
        p8 = by.get(8)
        if p8 and _diag_supportive(p8) and _architecture_supportive(p8):
            if abs(p8.recovery_fraction - best.recovery_fraction) <= 0.15:
                return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                    "Serovar 8/10: shared backbone without clear scdA vs funX → AMBIGUOUS."
                ]
        return True, None, extra + ["Serovar 10: MORE_BIOLOGY_REQUIRED — conservative support only."]

    # --- Serovar 11: HYBRID — never amtA alone ---
    if s == 11:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 11: amtA diagnostic not supportive."]
        if not _locus_context_ok(best, 11):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 11: amtA alone not permitted; neighborhood/locus-context required."
            ]
        if not _architecture_supportive(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 11: architecture neighborhood insufficient (not amtA alone)."
            ]
        rivals = _dominant_competing_diagnostics(
            list(by.values()), FAMILY_1_2_7_11, best, DEVELOPMENT_DEFAULT_COMPETING_DELTA
        )
        if rivals:
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                f"Serovar 11: family ties with {rivals} → AMBIGUOUS rather than forced number."
            ]
        return True, None, extra

    # --- Serovar 13: DIAGNOSTIC_REGION_DOMINANT (gltP) ---
    if s == 13:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 13: gltP diagnostic not supportive."]
        if _incomplete(best) and best.recovery_fraction < 0.35:
            return False, "AMBIGUOUS_ARCHITECTURE", extra
        return True, None, extra

    # --- Serovar 14: HYBRID — funAB + Region-2 ---
    if s == 14:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 14: funAB diagnostic not supportive."]
        if not _region2_ok(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 14: Region-2 incompleteness → AMBIGUOUS."
            ]
        for rival_s, gene in ((4, "wciP"), (15, "funI")):
            rp = by.get(rival_s)
            if rp and _diag_supportive(rp):
                return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                    f"Serovar 14: exclude opposite diagnostic anchor {gene} → AMBIGUOUS."
                ]
        return True, None, extra

    # --- Serovar 15: HYBRID — funI + Region-2 ---
    if s == 15:
        if not _diag_supportive(best):
            return False, None, extra + ["Serovar 15: funI diagnostic not supportive."]
        if not _region2_ok(best):
            return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                "Serovar 15: Region-2 incompleteness → AMBIGUOUS."
            ]
        for rival_s, gene in ((4, "wciP"), (14, "funAB")):
            rp = by.get(rival_s)
            if rp and _diag_supportive(rp):
                return False, "AMBIGUOUS_ARCHITECTURE", extra + [
                    f"Serovar 15: exclude opposite diagnostic anchor {gene} → AMBIGUOUS."
                ]
        return True, None, extra

    # Unknown serovar number — refuse
    return False, "AMBIGUOUS_ARCHITECTURE", extra + [f"No hybrid rule for serovar {s}."]


def interpret_profiles_hybrid(
    profiles: list[ArchitectureEvidenceProfile],
    *,
    species_status: str,
    capsule_detected: bool,
    reported_serovar: str | None = None,
    competing_delta: float = DEVELOPMENT_DEFAULT_COMPETING_DELTA,
) -> InterpretationResult:
    """Phase 5E hybrid interpretation of ArchitectureEvidenceProfile list.

    Decision hierarchy:
      1 species → 2 capsule locus → 3 diagnostic region → 4 architecture →
      5 competitor exclusion → 6 assembly → 7 integrate → 8 conservative interpretation

    Metadata ``reported_serovar`` is reporting-only and MUST NOT change the genomic call.
    """
    warnings: list[str] = []
    for p in profiles:
        warnings.extend(p.warnings)
    warnings.append("interpretation_mode=hybrid (Phase 5E / engine 0.2.1)")

    # 1 — species
    if species_status == "SPECIES_CHECK_FAILED":
        return _result(
            final_state="SPECIES_CHECK_FAILED",
            interpretation=(
                "Species check failed (Howell CDS homology proxy); "
                "no normal serovar architecture call emitted."
            ),
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
        )
    if species_status == "SPECIES_WEAK":
        warnings.append("Proceeding with SPECIES_WEAK warning; interpretation may be unreliable.")

    ranked = sorted(profiles, key=lambda p: p.recovery_fraction, reverse=True)
    by = _profile_by_sero(profiles)

    # 2 — capsule locus presence
    if not ranked or ranked[0].recovery_fraction <= 0 or not capsule_detected:
        return _result(
            final_state="NO_RECOGNIZED_CAPSULE_ARCHITECTURE",
            interpretation="No recognizable Howell capsule architecture recovered.",
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
        )

    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None

    # Insufficient sequence (global)
    if best.recovery_fraction < 0.25 and best.content_evidence in (
        "WEAK",
        "INDETERMINATE",
        "NOT_ASSESSABLE",
    ):
        total_rec = sum(
            (p.architecture.n_present + p.architecture.n_partial) if p.architecture else 0
            for p in profiles
        )
        if total_rec < 3:
            return _result(
                final_state="INSUFFICIENT_CAPSULE_SEQUENCE",
                interpretation="Capsule-associated evidence too incomplete for architecture interpretation.",
                warnings=warnings,
                reported=reported_serovar,
                species_status=species_status,
            )

    # 6 — assembly limitations (prefer ASSEMBLY_LIMITED over claiming absence)
    if best.architecture and best.architecture.assembly_limited:
        n_exp = best.architecture.n_expected or 1
        if best.architecture.n_not_observable / n_exp >= 0.3 and best.recovery_fraction < 0.75:
            return _result(
                final_state="ASSEMBLY_LIMITED",
                primary=str(best.serovar),
                interpretation=(
                    "Assembly quality limits capsule-architecture interpretation "
                    "(contig-edge / split-locus effects)."
                ),
                competing=[str(second.serovar)] if second else [],
                warnings=warnings,
                reported=reported_serovar,
                species_status=species_status,
            )

    # SPECIAL_CASE_5_12 — always combined call when 5/12 family wins
    if best.serovar in SPECIAL_CASE_5_12:
        if best.recovery_fraction >= 0.35:
            return _result(
                final_state="SEROVAR_5_OR_12",
                primary="5_OR_12",
                interpretation="5_OR_12-like",
                competing=["5", "12"],
                warnings=warnings
                + ["SPECIAL_CASE_5_12: never emit forced serovar 5 or 12 alone."],
                reported=reported_serovar,
                species_status=species_status,
                details={"interpretation_mode": "hybrid", "evidence_mode": "SPECIAL_CASE_5_12"},
            )

    # 5 — competitor exclusion (family-level)
    if (
        second is not None
        and (best.recovery_fraction - second.recovery_fraction) <= competing_delta
        and not (best.serovar in SPECIAL_CASE_5_12 and second.serovar in SPECIAL_CASE_5_12)
        and second.recovery_fraction >= 0.25
    ):
        # 1/2/7/11 family
        if best.serovar in FAMILY_1_2_7_11 and second.serovar in FAMILY_1_2_7_11:
            return _result(
                final_state="AMBIGUOUS_ARCHITECTURE",
                interpretation=(
                    f"Competing dominant targets in 1/2/7/11 family "
                    f"(best={best.serovar}@{best.recovery_fraction:.2f}, "
                    f"second={second.serovar}@{second.recovery_fraction:.2f})."
                ),
                competing=[str(best.serovar), str(second.serovar)],
                warnings=warnings,
                reported=reported_serovar,
                species_status=species_status,
            )
        # 4/14/15
        if best.serovar in FAMILY_4_14_15 and second.serovar in FAMILY_4_14_15:
            return _result(
                final_state="AMBIGUOUS_ARCHITECTURE",
                interpretation=(
                    f"Competing 4/14/15 diagnostic anchors "
                    f"(best={best.serovar}, second={second.serovar})."
                ),
                competing=[str(best.serovar), str(second.serovar)],
                warnings=warnings,
                reported=reported_serovar,
                species_status=species_status,
            )
        # 8/10 shared backbone
        if best.serovar in FAMILY_8_10 and second.serovar in FAMILY_8_10:
            return _result(
                final_state="AMBIGUOUS_ARCHITECTURE",
                interpretation=(
                    "Shared 8/10 backbone without clear scdA vs funX discrimination."
                ),
                competing=[str(best.serovar), str(second.serovar)],
                warnings=warnings,
                reported=reported_serovar,
                species_status=species_status,
            )
        # Generic close competition
        return _result(
            final_state="AMBIGUOUS_ARCHITECTURE",
            interpretation=(
                f"Competing architectures within DEVELOPMENT delta "
                f"(best={best.serovar}@{best.recovery_fraction:.2f}, "
                f"second={second.serovar}@{second.recovery_fraction:.2f})."
            ),
            competing=[str(best.serovar), str(second.serovar)],
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
        )

    # Conflicting: diagnostic strongly supports one, architecture another
    diag_best = max(profiles, key=lambda p: _diag_rank(p.diagnostic_evidence))
    if (
        _diag_supportive(diag_best)
        and diag_best.serovar != best.serovar
        and _architecture_supportive(best)
        and not (
            best.serovar in SPECIAL_CASE_5_12 and diag_best.serovar in SPECIAL_CASE_5_12
        )
        and not (best.serovar in FAMILY_1_2_7_11 and diag_best.serovar in FAMILY_1_2_7_11)
    ):
        return _result(
            final_state="CONFLICTING_GENOMIC_EVIDENCE",
            interpretation=(
                f"Diagnostic region favors serovar {diag_best.serovar} while architecture "
                f"content favors serovar {best.serovar}."
            ),
            competing=[str(best.serovar), str(diag_best.serovar)],
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
        )

    # Atypical: sequence present but no architecture fits
    if (
        best.recovery_fraction >= 0.35
        and best.content_evidence in ("WEAK", "INDETERMINATE")
        and all(p.recovery_fraction < DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT for p in profiles)
    ):
        return _result(
            final_state="ATYPICAL_CAPSULE_PROFILE",
            interpretation="Sufficient capsule sequence observed but no canonical Howell architecture fits cleanly.",
            competing=[str(p.serovar) for p in ranked[:3]],
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
        )

    # 3–5 / 7–8 — serovar-specific hybrid rules
    supported_ok, override, extra_w = _evaluate_serovar_support(best, by, warnings)
    warnings.extend(extra_w)

    if override:
        return _result(
            final_state=override,
            interpretation=(
                f"Hybrid rule for serovar {best.serovar} declined SUPPORTED; "
                f"state={override}."
            ),
            competing=[str(best.serovar)] + ([str(second.serovar)] if second else []),
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
            details={
                "interpretation_mode": "hybrid",
                "candidate_serovar": best.serovar,
                "recovery_fraction": best.recovery_fraction,
            },
        )

    if supported_ok:
        return _result(
            final_state="SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE",
            primary=str(best.serovar),
            interpretation=(
                f"Genomic capsule architecture is consistent with Howell serovar "
                f"{best.serovar}-associated reference architecture under Phase 5E hybrid rules "
                f"(recovery_fraction={best.recovery_fraction:.2f}; not a phenotypic call)."
            ),
            competing=[str(second.serovar)] if second else [],
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
            details={
                "interpretation_mode": "hybrid",
                "candidate_serovar": best.serovar,
                "recovery_fraction": best.recovery_fraction,
            },
        )

    # Conservative default
    if best.recovery_fraction >= DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT:
        return _result(
            final_state="AMBIGUOUS_ARCHITECTURE",
            interpretation=(
                f"Best architecture serovar {best.serovar} lacks Phase 5E hybrid support "
                f"for a SUPPORTED call; preferring AMBIGUOUS."
            ),
            competing=[str(best.serovar)] + ([str(second.serovar)] if second else []),
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
        )

    if best.recovery_fraction > 0:
        return _result(
            final_state="INSUFFICIENT_CAPSULE_SEQUENCE",
            interpretation="Insufficient capsule-locus recovery for a supported architecture association.",
            warnings=warnings,
            reported=reported_serovar,
            species_status=species_status,
        )

    return _result(
        final_state="NO_RECOGNIZED_CAPSULE_ARCHITECTURE",
        interpretation="No recognized Howell capsule architecture detected.",
        warnings=warnings,
        reported=reported_serovar,
        species_status=species_status,
    )
