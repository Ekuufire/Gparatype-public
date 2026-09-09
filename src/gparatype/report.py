"""Write human-readable, TSV, and JSON Gparatype reports."""

from __future__ import annotations

import json
from pathlib import Path

from gparatype.calling import console_summary
from gparatype.models import RunResult, TargetEvidence


def write_tsv(path: Path, sample: str, evidence: list[TargetEvidence]) -> None:
    cols = [
        "sample",
        "serovar",
        "target_gene",
        "target_accession",
        "reference_strain",
        "evidence_mode",
        "hit_status",
        "whole_cds_status",
        "whole_cds_identity",
        "whole_cds_coverage",
        "forward_primer_status",
        "reverse_primer_status",
        "primer_pair_status",
        "amplicon_status",
        "final_serovar_evidence_status",
        "evidence_notes",
        "percent_identity",
        "query_coverage",
        "alignment_length",
        "query_length",
        "mismatches",
        "gaps",
        "evalue",
        "bitscore",
        "contig",
        "subject_start",
        "subject_end",
        "strand",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(cols)]
    for e in evidence:
        row = [
            sample,
            str(e.serovar),
            e.target_gene,
            e.target_accession,
            e.reference_strain,
            e.evidence_mode or "",
            e.hit_status,
            e.whole_cds_status or e.hit_status,
            "" if e.whole_cds_identity is None else f"{e.whole_cds_identity:.3f}",
            "" if e.whole_cds_coverage is None else f"{e.whole_cds_coverage:.3f}",
            e.forward_primer_status or "",
            e.reverse_primer_status or "",
            e.primer_pair_status or "",
            e.amplicon_status or "",
            e.final_serovar_evidence_status or e.hit_status,
            e.evidence_notes or "",
            "" if e.percent_identity is None else f"{e.percent_identity:.3f}",
            "" if e.query_coverage is None else f"{e.query_coverage:.3f}",
            "" if e.alignment_length is None else str(e.alignment_length),
            "" if e.query_length is None else str(e.query_length),
            "" if e.mismatches is None else str(e.mismatches),
            "" if e.gaps is None else str(e.gaps),
            "" if e.evalue is None else f"{e.evalue:.3g}",
            "" if e.bitscore is None else f"{e.bitscore:.1f}",
            e.contig or "",
            "" if e.subject_start is None else str(e.subject_start),
            "" if e.subject_end is None else str(e.subject_end),
            e.strand or "",
        ]
        lines.append("\t".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, run: RunResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run.to_dict(), indent=2) + "\n", encoding="utf-8")


def write_text_report(path: Path, run: RunResult) -> None:
    call = run.call
    passing = [e for e in run.evidence if (e.final_serovar_evidence_status or e.hit_status) == "PASS"]
    primary = None
    if call.called_serovar is not None:
        primary = next((e for e in run.evidence if e.serovar == call.called_serovar), None)
    elif call.result_state == "SEROVAR_5_OR_12":
        primary = next((e for e in passing if e.serovar in (5, 12)), None)

    lines = [
        "Gparatype serovar target report (research prototype)",
        f"Version: {run.version}",
        f"Sample: {run.sample_name}",
        f"Input: {run.input_path}",
        f"Timestamp (UTC): {run.timestamp_utc}",
        f"Threshold label: {run.threshold_label}",
        f"DEVELOPMENT_THRESHOLD min_identity: {run.min_identity}",
        f"DEVELOPMENT_THRESHOLD min_coverage: {run.min_coverage}",
        "",
        f"Final result state: {call.result_state}",
        f"Called serovar: {call.called_serovar if call.called_serovar is not None else 'NA'}",
        f"Passing validated evidence (serovars): {','.join(str(s) for s in call.passing_serovars) or 'none'}",
        f"Number of validated PASS serovars: {len(passing)}",
        f"Console summary: {console_summary(call)}",
        "",
    ]
    if primary is not None:
        lines.extend(
            [
                "Primary target evidence:",
                f"  evidence_mode: {primary.evidence_mode}",
                f"  reference_strain: {primary.reference_strain}",
                f"  target_gene: {primary.target_gene}",
                f"  target_accession: {primary.target_accession}",
                f"  whole_cds_status: {primary.whole_cds_status or primary.hit_status}",
                f"  whole_cds_identity: {primary.whole_cds_identity or primary.percent_identity}",
                f"  whole_cds_coverage: {primary.whole_cds_coverage or primary.query_coverage}",
                f"  primer_pair_status: {primary.primer_pair_status}",
                f"  final_serovar_evidence_status: {primary.final_serovar_evidence_status}",
                f"  evidence_notes: {primary.evidence_notes}",
                "",
            ]
        )
    # Explicit hierarchy visibility for serovar 1 when whole-CDS present but diagnostic fails
    for e in run.evidence:
        if e.evidence_mode == "PRIMER_PATTERN" and e.whole_cds_status == "PASS" and e.final_serovar_evidence_status != "PASS":
            lines.append("Diagnostic hierarchy note (serovar with whole-CDS but failed primer pattern):")
            lines.append(
                f"  serovar {e.serovar} {e.target_gene}: whole_cds=PASS "
                f"(pident={e.whole_cds_identity}, qcov={e.whole_cds_coverage}); "
                f"primer_pair={e.primer_pair_status}; final={e.final_serovar_evidence_status}"
            )
            lines.append(f"  notes: {e.evidence_notes}")
            lines.append("")

    if call.result_state == "SEROVAR_5_OR_12" or any(
        e.serovar in (5, 12) and (e.final_serovar_evidence_status or e.hit_status) == "PASS" for e in run.evidence
    ):
        lines.append("5/12 special-case note:")
        lines.append(f"  {call.special_case_note or 'See documentation.'}")
        for e in run.evidence:
            if e.serovar in (5, 12):
                lines.append(
                    f"  serovar {e.serovar} {e.target_gene} {e.target_accession}: "
                    f"final={e.final_serovar_evidence_status or e.hit_status} "
                    f"pident={e.percent_identity} qcov={e.query_coverage}"
                )
        lines.append("")
    if call.warnings:
        lines.append("Warnings:")
        for w in call.warnings:
            lines.append(f"  - {w}")
        lines.append("")
    if call.error_message:
        lines.append(f"Error: {call.error_message}")
        lines.append("")
    lines.append(
        "NOTE: DEVELOPMENT_THRESHOLD values are engineering defaults only. "
        "This report does not claim sensitivity, specificity, or clinical performance."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_all_reports(output_dir: Path, run: RunResult) -> dict[str, Path]:
    base = output_dir / run.sample_name
    paths = {
        "txt": Path(str(base) + ".gparatype.txt"),
        "tsv": Path(str(base) + ".gparatype.tsv"),
        "json": Path(str(base) + ".gparatype.json"),
    }
    write_text_report(paths["txt"], run)
    write_tsv(paths["tsv"], run.sample_name, run.evidence)
    write_json(paths["json"], run)
    return paths
