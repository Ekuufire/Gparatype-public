"""Core Gparatype engine orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from gparatype import (
    DEVELOPMENT_THRESHOLD_MIN_COVERAGE,
    DEVELOPMENT_THRESHOLD_MIN_IDENTITY,
    __version__,
)
from gparatype.blast import run_blastn
from gparatype.calling import build_evidence, make_call
from gparatype.evidence import apply_evidence_hierarchy
from gparatype.models import CallResult, RunResult
from gparatype.report import write_all_reports
from gparatype.targets import load_target_registry
from gparatype.utils import sample_name_from_path, validate_nucleotide_fasta


def run_gparatype(
    input_fasta: Path,
    *,
    output_dir: Path,
    targets_fasta: Path | None = None,
    min_identity: float = DEVELOPMENT_THRESHOLD_MIN_IDENTITY,
    min_coverage: float = DEVELOPMENT_THRESHOLD_MIN_COVERAGE,
    keep_blast: bool = False,
    sample_name: str | None = None,
    apply_hierarchy: bool = True,
) -> RunResult:
    """Validate input, BLAST targets vs genome, apply evidence hierarchy, call, write reports."""
    input_fasta = Path(input_fasta)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    name = sample_name or sample_name_from_path(input_fasta)
    stamp = datetime.now(timezone.utc).isoformat()

    try:
        validate_nucleotide_fasta(input_fasta)
        registry = load_target_registry(targets_fasta)
        blast_path = output_dir / f"{name}.blast.tsv" if keep_blast else None
        hits, used_blast = run_blastn(registry.fasta_path, input_fasta, out_path=blast_path)

        evidence = build_evidence(
            list(registry),
            hits,
            min_identity=min_identity,
            min_coverage=min_coverage,
        )
        if apply_hierarchy:
            apply_evidence_hierarchy(evidence, input_fasta)

        call = make_call(evidence)
        run = RunResult(
            version=__version__,
            sample_name=name,
            input_path=str(input_fasta),
            timestamp_utc=stamp,
            min_identity=min_identity,
            min_coverage=min_coverage,
            threshold_label="DEVELOPMENT_THRESHOLD",
            call=call,
            evidence=evidence,
            blast_output_path=str(used_blast) if keep_blast else "",
        )
        if not keep_blast and used_blast.exists() and blast_path is None:
            try:
                used_blast.unlink()
            except OSError:
                pass
        write_all_reports(output_dir, run)
        return run
    except Exception as exc:  # noqa: BLE001
        call = CallResult(result_state="ERROR", error_message=str(exc))
        run = RunResult(
            version=__version__,
            sample_name=name,
            input_path=str(input_fasta),
            timestamp_utc=stamp,
            min_identity=min_identity,
            min_coverage=min_coverage,
            threshold_label="DEVELOPMENT_THRESHOLD",
            call=call,
            evidence=[],
        )
        write_all_reports(output_dir, run)
        return run
