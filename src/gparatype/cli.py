"""Command-line interface for Gparatype (engines: 0.2.1 hybrid default, 0.2 Phase5A, 0.1.1 baseline)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gparatype import (
    BASELINE_ENGINE_VERSION,
    DEVELOPMENT_THRESHOLD_MIN_COVERAGE,
    DEVELOPMENT_THRESHOLD_MIN_IDENTITY,
    HYBRID_ENGINE_VERSION,
    __version__,
)
from gparatype.calling import console_summary
from gparatype.engine import run_gparatype
from gparatype.utils import default_targets_fasta, project_root
from gparatype.v02.database import default_database_path
from gparatype.v02.engine import run_gparatype_v02


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gparatype",
        description=(
            "Gparatype v0.2.1 research prototype — architecture-aware capsule "
            "interpretation from whole-genome assembly FASTA (not FASTQ). "
            "Not for clinical use. Legacy engines 0.2 / 0.1.1 remain for "
            "reproducibility only."
        ),
    )
    p.add_argument("--input", "-i", required=True, type=Path, help="Input genome assembly FASTA")
    p.add_argument(
        "--engine",
        choices=["0.2.1", "0.2", "0.1.1"],
        default="0.2.1",
        help="Engine (default: 0.2.1 hybrid). Legacy: 0.2 (Phase 5A), 0.1.1 (baseline).",
    )
    p.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Output directory",
    )
    p.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Path to GparatypeDB directory (v0.2 / v0.2.1 only)",
    )
    p.add_argument(
        "--reported-serovar",
        type=str,
        default=None,
        help="Optional metadata serovar for reporting only (v0.2/v0.2.1; MUST NOT influence prediction)",
    )
    p.add_argument(
        "--targets",
        type=Path,
        default=None,
        help="Target FASTA for engine 0.1.1 (default: Phase 3A howell15 targets)",
    )
    p.add_argument(
        "--min-identity",
        type=float,
        default=DEVELOPMENT_THRESHOLD_MIN_IDENTITY,
        help="v0.1.1 DEVELOPMENT_THRESHOLD minimum percent identity (default: 90)",
    )
    p.add_argument(
        "--min-coverage",
        type=float,
        default=DEVELOPMENT_THRESHOLD_MIN_COVERAGE,
        help="v0.1.1 DEVELOPMENT_THRESHOLD minimum query coverage percent (default: 90)",
    )
    p.add_argument("--keep-blast", action="store_true", help="Retain BLAST TSV output")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument(
        "--version",
        action="version",
        version=(
            f"gparatype {__version__} (research prototype; "
            f"hybrid {HYBRID_ENGINE_VERSION}; "
            f"baseline engine {BASELINE_ENGINE_VERSION})"
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = project_root()
    sample = args.input.stem

    if args.engine == "0.1.1":
        out_dir = args.output_dir or (root / "results" / "phase3b" / sample)
        targets = args.targets or default_targets_fasta(root)
        if args.verbose:
            print(f"Gparatype {__version__} engine=0.1.1 baseline={BASELINE_ENGINE_VERSION}", file=sys.stderr)
            print(f"input={args.input}", file=sys.stderr)
            print(f"targets={targets}", file=sys.stderr)
            print(f"output_dir={out_dir}", file=sys.stderr)
        run = run_gparatype(
            args.input,
            output_dir=out_dir,
            targets_fasta=targets,
            min_identity=args.min_identity,
            min_coverage=args.min_coverage,
            keep_blast=args.keep_blast,
        )
        print(console_summary(run.call))
        return 1 if run.call.result_state == "ERROR" else 0

    # engine 0.2.1 (hybrid) or 0.2 (Phase 5A frozen)
    mode = "hybrid" if args.engine == "0.2.1" else "phase5a"
    default_phase = "phase5e" if mode == "hybrid" else "phase5a"
    out_dir = args.output_dir or (root / "results" / default_phase / sample)
    db = args.database or default_database_path()
    if args.verbose:
        print(
            f"Gparatype {__version__} engine={args.engine} "
            f"interpretation_mode={mode} (research prototype)",
            file=sys.stderr,
        )
        print(f"input={args.input}", file=sys.stderr)
        print(f"database={db}", file=sys.stderr)
        print(f"output_dir={out_dir}", file=sys.stderr)
    run = run_gparatype_v02(
        args.input,
        output_dir=out_dir,
        database=db,
        reported_serovar=args.reported_serovar,
        keep_blast=args.keep_blast,
        interpretation_mode=mode,
    )
    itp = run.interpretation
    print(
        f"{itp.final_state}\tprimary={itp.primary_architecture_serovar or '-'}\t"
        f"{itp.interpretation}"
    )
    return 1 if itp.final_state == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
