"""Data models for Gparatype v0.1 evidence and calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class TargetRecord:
    serovar: int
    gene: str
    accession: str
    reference_strain: str
    query_id: str
    sequence_length: int


@dataclass
class BlastHit:
    query_id: str
    subject_id: str
    percent_identity: float
    alignment_length: int
    mismatches: int
    gaps: int
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    evalue: float
    bitscore: float
    query_length: int
    query_coverage: float
    strand: str


@dataclass
class TargetEvidence:
    serovar: int
    target_gene: str
    target_accession: str
    reference_strain: str
    query_id: str
    hit_status: str  # PASS | PARTIAL | ABSENT (whole-CDS BLAST classification)
    percent_identity: Optional[float] = None
    query_coverage: Optional[float] = None
    alignment_length: Optional[int] = None
    query_length: Optional[int] = None
    mismatches: Optional[int] = None
    gaps: Optional[int] = None
    evalue: Optional[float] = None
    bitscore: Optional[float] = None
    contig: Optional[str] = None
    subject_start: Optional[int] = None
    subject_end: Optional[int] = None
    strand: Optional[str] = None
    # Phase 3C.1 evidence hierarchy fields
    evidence_mode: str = ""
    whole_cds_status: str = ""
    whole_cds_identity: Optional[float] = None
    whole_cds_coverage: Optional[float] = None
    forward_primer_status: str = ""
    reverse_primer_status: str = ""
    primer_pair_status: str = ""
    amplicon_status: str = ""
    final_serovar_evidence_status: str = ""
    evidence_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CallResult:
    result_state: str
    called_serovar: Optional[int] = None
    passing_serovars: list[int] = field(default_factory=list)
    special_case_note: str = ""
    warnings: list[str] = field(default_factory=list)
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunResult:
    version: str
    sample_name: str
    input_path: str
    timestamp_utc: str
    min_identity: float
    min_coverage: float
    threshold_label: str
    call: CallResult
    evidence: list[TargetEvidence]
    blast_output_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "sample_name": self.sample_name,
            "input_path": self.input_path,
            "timestamp_utc": self.timestamp_utc,
            "thresholds": {
                "label": self.threshold_label,
                "min_identity": self.min_identity,
                "min_coverage": self.min_coverage,
            },
            "call": self.call.to_dict(),
            "evidence": [e.to_dict() for e in self.evidence],
            "blast_output_path": self.blast_output_path,
        }
