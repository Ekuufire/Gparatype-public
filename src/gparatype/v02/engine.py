"""Gparatype v0.2 engine orchestration.

Supports:
  - interpretation_mode="phase5a" → frozen Phase 5A interpret_profiles (--engine 0.2)
  - interpretation_mode="hybrid"  → Phase 5E hybrid_interpretation (--engine 0.2.1)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from gparatype import __version__
from gparatype.utils import sample_name_from_path, validate_nucleotide_fasta
from gparatype.v02.architecture import build_architecture_profiles
from gparatype.v02.capsule_locator import locate_capsule
from gparatype.v02.constants import HYBRID_ENGINE, PHASE5A_ENGINE
from gparatype.v02.database import default_database_path, load_database
from gparatype.v02.diagnostic_regions import assess_diagnostic_regions
from gparatype.v02.evidence import assemble_evidence_profiles
from gparatype.v02.homology import run_homology
from gparatype.v02.hybrid_interpretation import interpret_profiles_hybrid
from gparatype.v02.interpretation import interpret_profiles
from gparatype.v02.models import InterpretationResult, V02RunResult
from gparatype.v02.report import write_v02_reports
from gparatype.v02.species import assess_species


def run_gparatype_v02(
    input_fasta: Path,
    output_dir: Path,
    database: Path | None = None,
    reported_serovar: str | None = None,
    keep_blast: bool = False,
    sample_name: str | None = None,
    interpretation_mode: str = "hybrid",
) -> V02RunResult:
    """Pipeline: validate → DB → homology → species → capsule → architecture →
    diagnostics → evidence → interpret → report.

    interpretation_mode:
      - "hybrid"  (default): Phase 5E hybrid rules (engine 0.2.1)
      - "phase5a": frozen Phase 5A interpret_profiles (engine 0.2)
    """
    mode = (interpretation_mode or "hybrid").strip().lower()
    if mode not in ("hybrid", "phase5a"):
        raise ValueError(f"Unsupported interpretation_mode={interpretation_mode!r}")

    input_fasta = Path(input_fasta)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    name = sample_name or sample_name_from_path(input_fasta)
    stamp = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    engine_id = HYBRID_ENGINE if mode == "hybrid" else PHASE5A_ENGINE

    try:
        fasta_info = validate_nucleotide_fasta(input_fasta)
        db_path = Path(database) if database else default_database_path()
        db = load_database(db_path)

        blast_path = output_dir / f"{name}.v02.blast.tsv" if keep_blast else None
        search_hits, _raw, used_blast = run_homology(input_fasta, db, out_path=blast_path)

        species_status, _n_acc, species_warnings = assess_species(search_hits)
        capsule_info = locate_capsule(search_hits)
        architectures = build_architecture_profiles(db, search_hits, input_fasta)
        diagnostics = assess_diagnostic_regions(db, search_hits)
        profiles = assemble_evidence_profiles(db, architectures, diagnostics)

        interpret_fn = interpret_profiles_hybrid if mode == "hybrid" else interpret_profiles
        capsule_detected = bool(capsule_info["capsule_detected"])
        if species_status == "SPECIES_CHECK_FAILED":
            capsule_detected = False

        interpretation = interpret_fn(
            profiles,
            species_status=species_status,
            capsule_detected=capsule_detected,
            reported_serovar=reported_serovar,
        )
        interpretation.warnings = list(dict.fromkeys(species_warnings + interpretation.warnings))
        if "interpretation_mode" not in interpretation.details:
            interpretation.details = {
                **interpretation.details,
                "interpretation_mode": mode,
            }

        runtime = time.perf_counter() - t0
        run = V02RunResult(
            software_version=__version__,
            engine=engine_id,
            database_version=db.version,
            database_checksum=db.checksum_manifest_sha256,
            sample_name=name,
            input_path=str(input_fasta),
            timestamp_utc=stamp,
            contig_count=int(fasta_info["n_records"]),
            runtime_seconds=runtime,
            species_status=species_status,
            capsule_detected=bool(capsule_info["capsule_detected"]),
            interpretation=interpretation,
            profiles=profiles,
            component_hits=search_hits,
            blast_output_path=str(used_blast) if keep_blast else "",
            reported_serovar=reported_serovar or "",
            interpretation_mode=mode,
        )
        if not keep_blast and used_blast.exists() and blast_path is None:
            try:
                used_blast.unlink()
            except OSError:
                pass
        write_v02_reports(output_dir, run)
        return run
    except Exception as exc:  # noqa: BLE001
        runtime = time.perf_counter() - t0
        interpretation = InterpretationResult(
            final_state="ERROR",
            primary_architecture_serovar="",
            interpretation=f"Technical error: {exc}",
            warnings=[],
            metadata_agreement="NOT_SUPPLIED",
            species_status="",
            details={"interpretation_mode": mode},
        )
        run = V02RunResult(
            software_version=__version__,
            engine=engine_id,
            database_version="",
            database_checksum="",
            sample_name=name,
            input_path=str(input_fasta),
            timestamp_utc=stamp,
            contig_count=0,
            runtime_seconds=runtime,
            species_status="",
            capsule_detected=False,
            interpretation=interpretation,
            profiles=[],
            component_hits=[],
            reported_serovar=reported_serovar or "",
            error_message=str(exc),
            interpretation_mode=mode,
        )
        write_v02_reports(output_dir, run)
        return run


def run_gparatype_v021(
    input_fasta: Path,
    output_dir: Path,
    database: Path | None = None,
    reported_serovar: str | None = None,
    keep_blast: bool = False,
    sample_name: str | None = None,
) -> V02RunResult:
    """Convenience runner for Phase 5E hybrid engine 0.2.1."""
    return run_gparatype_v02(
        input_fasta,
        output_dir,
        database=database,
        reported_serovar=reported_serovar,
        keep_blast=keep_blast,
        sample_name=sample_name,
        interpretation_mode="hybrid",
    )
