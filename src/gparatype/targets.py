"""Load and register Howell 15-target molecular references."""

from __future__ import annotations

import re
from pathlib import Path

from gparatype.models import TargetRecord
from gparatype.utils import default_targets_fasta, parse_fasta

HEADER_RE = re.compile(
    r"^serovar_(\d+)\|strain=([^|]+)\|gene=([^|]+)\|accession=([A-Z0-9_.]+)$",
    re.IGNORECASE,
)


class TargetRegistry:
    def __init__(self, targets: list[TargetRecord], fasta_path: Path):
        self.targets = targets
        self.fasta_path = fasta_path
        self.by_query_id = {t.query_id: t for t in targets}
        self.by_serovar = {t.serovar: t for t in targets}

    def __len__(self) -> int:
        return len(self.targets)

    def __iter__(self):
        return iter(self.targets)


def parse_target_header(header: str) -> tuple[int, str, str, str]:
    """Parse standardized Phase 3A header; returns serovar, strain, gene, accession."""
    token = header.split()[0]
    m = HEADER_RE.match(token)
    if not m:
        raise ValueError(f"Unrecognized target FASTA header: {header}")
    serovar = int(m.group(1))
    strain = m.group(2).replace(".", ".")  # keep as-is (No.4 style)
    # Restore common display: No.4 stored without space
    gene = m.group(3)
    accession = m.group(4)
    return serovar, strain, gene, accession


def load_target_registry(fasta_path: Path | None = None) -> TargetRegistry:
    path = Path(fasta_path) if fasta_path else default_targets_fasta()
    if not path.is_file():
        raise FileNotFoundError(f"Target database not found: {path}")
    records = parse_fasta(path)
    targets: list[TargetRecord] = []
    seen_sero: set[int] = set()
    for header, seq in records:
        serovar, strain, gene, accession = parse_target_header(header)
        if serovar in seen_sero:
            raise ValueError(f"Duplicate serovar target in database: {serovar}")
        seen_sero.add(serovar)
        query_id = header.split()[0]
        targets.append(
            TargetRecord(
                serovar=serovar,
                gene=gene,
                accession=accession,
                reference_strain=strain,
                query_id=query_id,
                sequence_length=len(seq),
            )
        )
    if len(targets) != 15:
        raise ValueError(f"Expected 15 targets, found {len(targets)} in {path}")
    targets.sort(key=lambda t: t.serovar)
    return TargetRegistry(targets, path)
