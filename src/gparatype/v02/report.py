"""Write Gparatype v0.2 research-prototype reports."""

from __future__ import annotations

import json
from pathlib import Path

from gparatype.v02.models import V02RunResult


def write_v02_reports(output_dir: Path, run: V02RunResult) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sample = run.sample_name
    _write_txt(output_dir / f"{sample}.gparatype_v02.txt", run)
    _write_summary_tsv(output_dir / "summary.tsv", run)
    _write_architecture_tsv(output_dir / "architecture_evidence.tsv", run)
    _write_component_tsv(output_dir / "component_evidence.tsv", run)
    _write_json(output_dir / f"{sample}.gparatype_v02.json", run)


def _write_txt(path: Path, run: V02RunResult) -> None:
    itp = run.interpretation
    lines = [
        "Gparatype v0.2 — RESEARCH PROTOTYPE",
        "Not for clinical use. Not a validated phenotypic serovar assay.",
        "",
        f"software_version\t{run.software_version}",
        f"engine\t{run.engine}",
        f"interpretation_mode\t{run.interpretation_mode or run.interpretation.details.get('interpretation_mode', '')}",
        f"database_version\t{run.database_version}",
        f"database_checksum\t{run.database_checksum}",
        f"sample\t{run.sample_name}",
        f"input\t{run.input_path}",
        f"timestamp_utc\t{run.timestamp_utc}",
        f"contig_count\t{run.contig_count}",
        f"runtime_seconds\t{run.runtime_seconds:.3f}",
        f"species_status\t{run.species_status}",
        f"capsule_detected\t{run.capsule_detected}",
        f"reported_serovar\t{run.reported_serovar or 'NOT_SUPPLIED'}",
        "",
        f"final_state\t{itp.final_state}",
        f"primary_architecture\t{itp.primary_architecture_serovar}",
        f"interpretation\t{itp.interpretation}",
        f"competing_serovars\t{','.join(itp.competing_serovars)}",
        f"metadata_agreement\t{itp.metadata_agreement}",
        "",
        "Evidence summary (qualitative dims; recovery_fraction is descriptive, not a probability):",
    ]
    for p in sorted(run.profiles, key=lambda x: x.recovery_fraction, reverse=True):
        lines.append(
            f"  serovar {p.serovar}: recovery={p.recovery_fraction:.3f} "
            f"content={p.content_evidence} seq={p.sequence_evidence} "
            f"order={p.order_evidence} adj={p.adjacency_evidence} "
            f"ori={p.orientation_evidence} diag={p.diagnostic_evidence} "
            f"complete={p.completeness_evidence} assembly={p.assembly_limitations} "
            f"mode={p.evidence_mode}"
        )
        if p.architecture:
            lines.append(
                f"    present={p.architecture.n_present} partial={p.architecture.n_partial} "
                f"not_detected={p.architecture.n_not_detected} "
                f"not_observable={p.architecture.n_not_observable}"
            )
    lines.append("")
    lines.append("Warnings / limitations:")
    for w in itp.warnings:
        lines.append(f"  - {w}")
    if run.error_message:
        lines.append(f"ERROR: {run.error_message}")
    lines.append("")
    lines.append(
        "SEARCH thresholds retain technical hits; DEVELOPMENT_DEFAULT labels are not "
        "the v0.1 90/90 call rule and are not biologically optimized."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_tsv(path: Path, run: V02RunResult) -> None:
    itp = run.interpretation
    header = [
        "sample",
        "software_version",
        "engine",
        "interpretation_mode",
        "database_version",
        "database_checksum",
        "final_state",
        "primary_architecture",
        "interpretation",
        "competing_serovars",
        "species_status",
        "capsule_detected",
        "metadata_agreement",
        "reported_serovar",
        "contig_count",
        "runtime_seconds",
    ]
    row = [
        run.sample_name,
        run.software_version,
        run.engine,
        run.interpretation_mode
        or str(run.interpretation.details.get("interpretation_mode", "")),
        run.database_version,
        run.database_checksum,
        itp.final_state,
        itp.primary_architecture_serovar,
        itp.interpretation.replace("\t", " "),
        ";".join(itp.competing_serovars),
        run.species_status,
        str(run.capsule_detected),
        itp.metadata_agreement,
        run.reported_serovar or "",
        str(run.contig_count),
        f"{run.runtime_seconds:.3f}",
    ]
    path.write_text("\t".join(header) + "\n" + "\t".join(row) + "\n", encoding="utf-8")


def _write_architecture_tsv(path: Path, run: V02RunResult) -> None:
    header = [
        "sample",
        "serovar",
        "reference_strain",
        "evidence_mode",
        "readiness",
        "recovery_fraction",
        "content_evidence",
        "sequence_evidence",
        "order_evidence",
        "adjacency_evidence",
        "orientation_evidence",
        "diagnostic_evidence",
        "completeness_evidence",
        "assembly_limitations",
        "competing_evidence",
        "n_present",
        "n_partial",
        "n_not_detected",
        "n_not_observable",
    ]
    lines = ["\t".join(header)]
    for p in run.profiles:
        arch = p.architecture
        lines.append(
            "\t".join(
                [
                    run.sample_name,
                    str(p.serovar),
                    p.reference_strain,
                    p.evidence_mode,
                    p.readiness,
                    f"{p.recovery_fraction:.4f}",
                    p.content_evidence,
                    p.sequence_evidence,
                    p.order_evidence,
                    p.adjacency_evidence,
                    p.orientation_evidence,
                    p.diagnostic_evidence,
                    p.completeness_evidence,
                    p.assembly_limitations,
                    p.competing_evidence,
                    str(arch.n_present if arch else 0),
                    str(arch.n_partial if arch else 0),
                    str(arch.n_not_detected if arch else 0),
                    str(arch.n_not_observable if arch else 0),
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_component_tsv(path: Path, run: V02RunResult) -> None:
    header = [
        "sample",
        "serovar",
        "component_id",
        "gene",
        "accession",
        "gene_order",
        "status",
        "percent_identity",
        "query_coverage",
        "contig",
        "subject_start",
        "subject_end",
        "strand",
        "near_contig_edge",
    ]
    lines = ["\t".join(header)]
    for p in run.profiles:
        if not p.architecture:
            continue
        for c in p.architecture.components:
            lines.append(
                "\t".join(
                    [
                        run.sample_name,
                        str(c.serovar),
                        c.component_id,
                        c.gene,
                        c.accession,
                        str(c.gene_order),
                        c.status,
                        "" if c.percent_identity is None else f"{c.percent_identity:.3f}",
                        "" if c.query_coverage is None else f"{c.query_coverage:.3f}",
                        c.contig,
                        "" if c.subject_start is None else str(c.subject_start),
                        "" if c.subject_end is None else str(c.subject_end),
                        c.strand,
                        str(c.near_contig_edge),
                    ]
                )
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, run: V02RunResult) -> None:
    itp = run.interpretation
    payload = {
        "software_version": run.software_version,
        "engine": run.engine,
        "interpretation_mode": run.interpretation_mode
        or run.interpretation.details.get("interpretation_mode", ""),
        "database_version": run.database_version,
        "database_checksum": run.database_checksum,
        "sample_name": run.sample_name,
        "input_path": run.input_path,
        "timestamp_utc": run.timestamp_utc,
        "contig_count": run.contig_count,
        "runtime_seconds": run.runtime_seconds,
        "species_status": run.species_status,
        "capsule_detected": run.capsule_detected,
        "reported_serovar": run.reported_serovar,
        "interpretation": {
            "final_state": itp.final_state,
            "primary_architecture_serovar": itp.primary_architecture_serovar,
            "interpretation": itp.interpretation,
            "competing_serovars": itp.competing_serovars,
            "warnings": itp.warnings,
            "metadata_agreement": itp.metadata_agreement,
            "species_status": itp.species_status,
            "details": itp.details,
        },
        "profiles": [
            {
                "serovar": p.serovar,
                "recovery_fraction": p.recovery_fraction,
                "content_evidence": p.content_evidence,
                "sequence_evidence": p.sequence_evidence,
                "order_evidence": p.order_evidence,
                "adjacency_evidence": p.adjacency_evidence,
                "orientation_evidence": p.orientation_evidence,
                "diagnostic_evidence": p.diagnostic_evidence,
                "completeness_evidence": p.completeness_evidence,
                "assembly_limitations": p.assembly_limitations,
                "evidence_mode": p.evidence_mode,
                "readiness": p.readiness,
            }
            for p in run.profiles
        ],
        "error_message": run.error_message,
        "disclaimer": (
            "RESEARCH PROTOTYPE — not for clinical use; not a validated phenotypic serovar call."
        ),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
