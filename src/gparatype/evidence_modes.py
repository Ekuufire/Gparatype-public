"""Load per-serovar evidence-mode configuration."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from gparatype.utils import project_root


@dataclass(frozen=True)
class EvidenceModeConfig:
    serovar: int
    target_gene: str
    target_accession: str
    evidence_mode: str
    special_case: bool
    source_phase: str
    notes: str


def default_modes_path(root: Path | None = None) -> Path:
    root = root or project_root()
    return root / "config" / "serovar_evidence_modes.tsv"


def load_evidence_modes(path: Path | None = None) -> dict[int, EvidenceModeConfig]:
    p = Path(path) if path else default_modes_path()
    if not p.is_file():
        raise FileNotFoundError(f"Evidence mode config not found: {p}")
    out: dict[int, EvidenceModeConfig] = {}
    for r in csv.DictReader(p.open(encoding="utf-8"), delimiter="\t"):
        sero = int(r["serovar"])
        out[sero] = EvidenceModeConfig(
            serovar=sero,
            target_gene=r["target_gene"],
            target_accession=r["target_accession"],
            evidence_mode=r["evidence_mode"].strip().upper(),
            special_case=r.get("special_case", "NO").strip().upper() in ("YES", "TRUE", "1"),
            source_phase=r.get("source_phase", ""),
            notes=r.get("notes", ""),
        )
    if len(out) != 15:
        raise ValueError(f"Expected 15 evidence-mode rows, found {len(out)}")
    return out


def load_primer_table(root: Path | None = None) -> dict[str, dict]:
    root = root or project_root()
    path = root / "data" / "curated" / "phase2d1_howell_molecular_serotyping_targets.tsv"
    rows = {}
    for r in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"):
        rows[r["serovar_call"]] = r
    return rows
