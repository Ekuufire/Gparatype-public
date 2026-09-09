"""Per-serovar evidence hierarchy evaluation (Phase 3C.1).

Does not hard-code strain/assembly exceptions.
"""

from __future__ import annotations

from pathlib import Path

from gparatype.diagnostics import find_primer_on_sequence, predict_pcr_products
from gparatype.evidence_modes import EvidenceModeConfig, load_evidence_modes, load_primer_table
from gparatype.models import TargetEvidence
from gparatype.utils import parse_fasta, project_root


def _assay_key(serovar: int) -> str:
    if serovar in (5, 12):
        return "5_or_12"
    return str(serovar)


def evaluate_primer_pair_on_genome(
    genome_fasta: Path,
    forward: str,
    reverse: str,
    expected_bp: int,
) -> dict:
    records = parse_fasta(genome_fasta)
    contig_map = {h.split()[0]: s for h, s in records}
    fwd_plus = False
    rev_minus = False
    for seq in contig_map.values():
        if any(h.strand == "plus" for h in find_primer_on_sequence(seq, forward, 0)):
            fwd_plus = True
        if any(h.strand == "minus" for h in find_primer_on_sequence(seq, reverse, 0)):
            rev_minus = True
    products = predict_pcr_products(contig_map, forward, reverse, expected_bp, max_mismatch=0)
    size_ok = [p for p in products if p["size_ok"]]
    if size_ok:
        best = min(size_ok, key=lambda p: abs(p["predicted_product_bp"] - expected_bp))
        return {
            "forward_primer_status": "PRESENT",
            "reverse_primer_status": "PRESENT",
            "primer_pair_status": "EXPECTED_PRODUCT",
            "predicted_product_bp": best["predicted_product_bp"],
            "notes": f"in-silico product {best['predicted_product_bp']} bp (expected {expected_bp})",
        }
    if fwd_plus and rev_minus and products:
        return {
            "forward_primer_status": "PRESENT",
            "reverse_primer_status": "PRESENT",
            "primer_pair_status": "IMPLAUSIBLE_DISTANCE",
            "predicted_product_bp": products[0]["predicted_product_bp"],
            "notes": "primers present but product size outside tolerance",
        }
    if fwd_plus and rev_minus:
        return {
            "forward_primer_status": "PRESENT",
            "reverse_primer_status": "PRESENT",
            "primer_pair_status": "WRONG_ORIENTATION_OR_FAR",
            "predicted_product_bp": None,
            "notes": "both primers found but no oriented product",
        }
    if fwd_plus and not rev_minus:
        return {
            "forward_primer_status": "PRESENT",
            "reverse_primer_status": "ABSENT",
            "primer_pair_status": "FORWARD_ONLY",
            "predicted_product_bp": None,
            "notes": "",
        }
    if rev_minus and not fwd_plus:
        return {
            "forward_primer_status": "ABSENT",
            "reverse_primer_status": "PRESENT",
            "primer_pair_status": "REVERSE_ONLY",
            "predicted_product_bp": None,
            "notes": "",
        }
    return {
        "forward_primer_status": "ABSENT",
        "reverse_primer_status": "ABSENT",
        "primer_pair_status": "ABSENT",
        "predicted_product_bp": None,
        "notes": "",
    }


def apply_evidence_hierarchy(
    evidence: list[TargetEvidence],
    genome_fasta: Path,
    *,
    modes: dict[int, EvidenceModeConfig] | None = None,
    root: Path | None = None,
) -> list[TargetEvidence]:
    """Enrich TargetEvidence with mode-aware final status. Generic — no strain IDs."""
    root = root or project_root()
    modes = modes or load_evidence_modes()
    primers = load_primer_table(root)

    for e in evidence:
        cfg = modes[e.serovar]
        e.evidence_mode = cfg.evidence_mode
        e.whole_cds_status = e.hit_status
        e.whole_cds_identity = e.percent_identity
        e.whole_cds_coverage = e.query_coverage

        assay = _assay_key(e.serovar)
        pr = primers.get(assay)
        if pr is None:
            e.forward_primer_status = "NA"
            e.reverse_primer_status = "NA"
            e.primer_pair_status = "NA"
            primer_ok = False
            primer_note = "no primer row"
        else:
            pret = evaluate_primer_pair_on_genome(
                genome_fasta,
                pr["forward_primer_sequence"],
                pr["reverse_primer_sequence"],
                int(pr["expected_amplicon_bp"]),
            )
            e.forward_primer_status = pret["forward_primer_status"]
            e.reverse_primer_status = pret["reverse_primer_status"]
            e.primer_pair_status = pret["primer_pair_status"]
            primer_ok = pret["primer_pair_status"] == "EXPECTED_PRODUCT"
            primer_note = pret["notes"]

        # Amplicon status: optional; NA unless we BLAST diagnostic region (kept light in 3C.1)
        e.amplicon_status = "NA"
        notes = []
        if cfg.notes:
            notes.append(cfg.notes)
        if primer_note:
            notes.append(primer_note)

        mode = cfg.evidence_mode
        if mode == "PRIMER_PATTERN":
            # Whole-CDS alone is insufficient
            if primer_ok:
                e.final_serovar_evidence_status = "PASS"
                notes.append("diagnostic primer-pair architecture present")
            elif e.whole_cds_status == "PASS":
                e.final_serovar_evidence_status = "FAIL"
                notes.append(
                    "whole-CDS homolog present but Howell primer-pair pattern ABSENT; "
                    "whole-CDS not sufficient under PRIMER_PATTERN mode"
                )
            elif e.whole_cds_status == "PARTIAL" or e.primer_pair_status in (
                "FORWARD_ONLY",
                "REVERSE_ONLY",
                "IMPLAUSIBLE_DISTANCE",
            ):
                e.final_serovar_evidence_status = "PARTIAL"
            else:
                e.final_serovar_evidence_status = "ABSENT"
        elif mode == "AMPLICON_REGION":
            # Prefer amplicon; fall back unavailable → treat like whole CDS with note
            e.final_serovar_evidence_status = e.whole_cds_status if e.whole_cds_status != "PASS" else "PASS"
            if e.amplicon_status == "NA":
                notes.append("AMPLICON_REGION configured but amplicon BLAST not required when WHOLE_CDS supports panel")
                e.final_serovar_evidence_status = e.whole_cds_status
        elif mode == "SPECIAL_CASE":
            # Shared 5/12: whole-CDS pass contributes to SEROVAR_5_OR_12 pool
            e.final_serovar_evidence_status = e.whole_cds_status
            notes.append("SPECIAL_CASE shared wcwK; no direct 5 vs 12 call")
        elif mode == "COMBINED":
            # Not used in 3C.1 recommendations; require both CDS and primer if ever set
            if e.whole_cds_status == "PASS" and primer_ok:
                e.final_serovar_evidence_status = "PASS"
            elif e.whole_cds_status == "PASS" or primer_ok:
                e.final_serovar_evidence_status = "PARTIAL"
            else:
                e.final_serovar_evidence_status = e.whole_cds_status
        else:
            # WHOLE_CDS
            e.final_serovar_evidence_status = e.whole_cds_status
            if e.serovar == 6:
                notes.append("ASSAY_REGION_UNRESOLVED")

        e.evidence_notes = "; ".join(n for n in notes if n)

    return evidence
