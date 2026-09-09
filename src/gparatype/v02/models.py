"""Dataclasses for Gparatype v0.2 evidence objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComponentHit:
    component_id: str
    serovar: int
    gene: str
    accession: str
    contig: str
    subject_start: int
    subject_end: int
    strand: str
    percent_identity: float
    query_coverage: float
    alignment_length: int
    mismatches: int
    gaps: int
    bitscore: float
    evalue: float
    hit_count: int = 1
    query_length: int = 0


@dataclass
class ComponentStatus:
    component_id: str
    serovar: int
    gene: str
    accession: str
    gene_order: int
    status: str  # PRESENT / PARTIAL / NOT_DETECTED / NOT_OBSERVABLE
    percent_identity: float | None = None
    query_coverage: float | None = None
    contig: str = ""
    subject_start: int | None = None
    subject_end: int | None = None
    strand: str = ""
    near_contig_edge: bool = False


@dataclass
class ArchitectureProfile:
    serovar: int
    reference_strain: str
    n_expected: int
    n_present: int
    n_partial: int
    n_not_detected: int
    n_not_observable: int
    recovery_fraction: float
    order_status: str
    adjacency_status: str
    orientation_status: str
    assembly_limited: bool
    components: list[ComponentStatus] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DiagnosticEvidence:
    serovar: int
    gene: str
    accession: str
    status: str  # STRONG/MODERATE/WEAK/ABSENT/DIVERGENT/NOT_ASSESSABLE
    percent_identity: float | None = None
    query_coverage: float | None = None
    contig: str = ""


@dataclass
class ArchitectureEvidenceProfile:
    serovar: int
    reference_strain: str
    evidence_mode: str
    readiness: str
    content_evidence: str
    sequence_evidence: str
    order_evidence: str
    adjacency_evidence: str
    orientation_evidence: str
    diagnostic_evidence: str
    completeness_evidence: str
    assembly_limitations: str
    competing_evidence: str
    recovery_fraction: float
    warnings: list[str] = field(default_factory=list)
    architecture: ArchitectureProfile | None = None
    diagnostic: DiagnosticEvidence | None = None


@dataclass
class InterpretationResult:
    final_state: str
    primary_architecture_serovar: str  # number, "5_OR_12", or empty
    interpretation: str
    competing_serovars: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata_agreement: str = "NOT_SUPPLIED"
    species_status: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class V02RunResult:
    software_version: str
    engine: str
    database_version: str
    database_checksum: str
    sample_name: str
    input_path: str
    timestamp_utc: str
    contig_count: int
    runtime_seconds: float
    species_status: str
    capsule_detected: bool
    interpretation: InterpretationResult
    profiles: list[ArchitectureEvidenceProfile]
    component_hits: list[ComponentHit]
    blast_output_path: str = ""
    reported_serovar: str = ""
    error_message: str = ""
    interpretation_mode: str = ""  # "phase5a" | "hybrid"
