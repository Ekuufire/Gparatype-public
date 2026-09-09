"""BLASTN wrappers for Gparatype v0.1 target search."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from gparatype.models import BlastHit

# Explicit outfmt 6 fields (machine-readable only)
BLAST_FIELDS = [
    "qseqid",
    "sseqid",
    "pident",
    "length",
    "mismatch",
    "gapopen",
    "qstart",
    "qend",
    "sstart",
    "send",
    "evalue",
    "bitscore",
    "qlen",
]
OUTFMT = "6 " + " ".join(BLAST_FIELDS)


def blastn_available() -> bool:
    return shutil.which("blastn") is not None


def parse_blast_tsv(text: str) -> list[BlastHit]:
    hits: list[BlastHit] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 13:
            raise ValueError(f"Unexpected BLAST row (need 13 fields): {line}")
        qlen = int(parts[12])
        aln = int(parts[3])
        qcov = (100.0 * aln / qlen) if qlen > 0 else 0.0
        sstart = int(parts[8])
        send = int(parts[9])
        strand = "plus" if sstart <= send else "minus"
        hits.append(
            BlastHit(
                query_id=parts[0],
                subject_id=parts[1],
                percent_identity=float(parts[2]),
                alignment_length=aln,
                mismatches=int(parts[4]),
                gaps=int(parts[5]),
                query_start=int(parts[6]),
                query_end=int(parts[7]),
                subject_start=sstart,
                subject_end=send,
                evalue=float(parts[10]),
                bitscore=float(parts[11]),
                query_length=qlen,
                query_coverage=qcov,
                strand=strand,
            )
        )
    return hits


def run_blastn(
    query_fasta: Path,
    subject_fasta: Path,
    *,
    out_path: Path | None = None,
    evalue: float = 1e-5,
) -> tuple[list[BlastHit], Path]:
    """Search query targets against subject genome. Returns hits and TSV path."""
    if not blastn_available():
        raise RuntimeError(
            "NCBI BLAST+ 'blastn' not found on PATH. "
            "Install BLAST+ and ensure the blastn executable is available "
            "(https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs&DOC_TYPE=Download)."
        )
    if out_path is None:
        tmp = tempfile.NamedTemporaryFile(prefix="gparatype_blast_", suffix=".tsv", delete=False)
        out_path = Path(tmp.name)
        tmp.close()
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "blastn",
        "-query",
        str(query_fasta),
        "-subject",
        str(subject_fasta),
        "-task",
        "blastn",
        "-evalue",
        str(evalue),
        "-outfmt",
        OUTFMT,
        "-out",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"blastn failed (exit {proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )
    text = out_path.read_text(encoding="utf-8", errors="replace")
    return parse_blast_tsv(text), out_path
