"""Utility helpers: paths, FASTA I/O, alphabet checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

NUCLEOTIDE_RE = re.compile(r"^[ACGTRYSWKMBDHVN]+$", re.IGNORECASE)


def project_root() -> Path:
    """Locate distribution root containing data/gparatype_db (or reference_sequences)."""
    here = Path(__file__).resolve()
    for parent in [here.parents[i] for i in range(2, min(6, len(here.parents)))]:
        if (parent / "data" / "gparatype_db").is_dir():
            return parent
        if (parent / "data" / "reference_sequences").is_dir():
            return parent
    cwd = Path.cwd()
    if (cwd / "data" / "gparatype_db").is_dir():
        return cwd
    if (cwd / "data" / "reference_sequences").is_dir():
        return cwd
    return cwd


def default_targets_fasta(root: Path | None = None) -> Path:
    root = root or project_root()
    return root / "data" / "reference_sequences" / "molecular_targets" / "gparatype_howell15_targets.fasta"


def sample_name_from_path(path: Path) -> str:
    name = path.name
    for ext in (".fasta", ".fa", ".fna", ".fas"):
        if name.lower().endswith(ext):
            return name[: -len(ext)]
    return path.stem


def parse_fasta(path: Path) -> list[tuple[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Input FASTA not found: {path}")
    records: list[tuple[str, str]] = []
    header: str | None = None
    chunks: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n\r")
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(chunks)))
                header = line[1:].strip() or "unnamed"
                chunks = []
            else:
                if header is None:
                    raise ValueError("Malformed FASTA: sequence before header")
                chunks.append(line.strip().replace(" ", "").upper())
        if header is not None:
            records.append((header, "".join(chunks)))
    if not records:
        raise ValueError("Malformed FASTA: no sequence records")
    return records


def validate_nucleotide_fasta(path: Path) -> dict:
    """Validate input assembly FASTA. Raises ValueError on failure."""
    records = parse_fasta(path)
    total = 0
    for hdr, seq in records:
        if not seq:
            raise ValueError(f"Empty sequence for record: {hdr}")
        if not NUCLEOTIDE_RE.match(seq):
            bad = sorted({c for c in seq if c not in "ACGTRYSWKMBDHVN"})
            raise ValueError(f"Invalid nucleotide alphabet in {hdr}: {bad[:10]}")
        total += len(seq)
    if total <= 0:
        raise ValueError("Total sequence length is 0")
    return {
        "n_records": len(records),
        "total_length": total,
        "headers": [h.split()[0] for h, _ in records],
    }


def write_fasta(path: Path, records: Iterable[tuple[str, str]], width: int = 70) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for header, seq in records:
            fh.write(f">{header}\n")
            for i in range(0, len(seq), width):
                fh.write(seq[i : i + width] + "\n")
