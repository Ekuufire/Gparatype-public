"""GparatypeDB loader and validator (v0.2)."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SerovarRecord:
    serovar: int
    strain: str
    aliases: str
    special_case: str
    evidence_mode: str
    readiness: str


@dataclass
class ComponentRecord:
    component_id: str
    serovar: int
    reference_strain: str
    gene_name: str
    aliases: str
    accession: str
    gene_order: int
    orientation: str
    sequence_length: int
    upstream_neighbor: str
    downstream_neighbor: str
    source_publication: str
    doi: str
    local_fasta: str
    sequence_sha256: str
    notes: str = ""


@dataclass
class DiagnosticTarget:
    serovar: int
    gene: str
    accession: str
    aliases: str
    source: str
    notes: str = ""


@dataclass
class SpecialCase:
    case_id: str
    serovars: list[int]
    description: str
    rule: str


@dataclass
class GparatypeDatabase:
    path: Path
    version: str
    checksum_manifest_sha256: str
    serovars: dict[int, SerovarRecord] = field(default_factory=dict)
    components: list[ComponentRecord] = field(default_factory=list)
    components_by_accession: dict[str, ComponentRecord] = field(default_factory=dict)
    components_by_serovar: dict[int, list[ComponentRecord]] = field(default_factory=dict)
    architectures_long: list[dict[str, str]] = field(default_factory=list)
    gene_aliases: list[dict[str, str]] = field(default_factory=list)
    diagnostic_targets: dict[int, DiagnosticTarget] = field(default_factory=dict)
    special_cases: list[SpecialCase] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    fasta_path: Path | None = None
    modes: dict[int, dict[str, str]] = field(default_factory=dict)
    result_states: list[dict[str, str]] = field(default_factory=list)

    def architecture_for(self, serovar: int) -> list[ComponentRecord]:
        return sorted(
            self.components_by_serovar.get(serovar, []),
            key=lambda c: c.gene_order,
        )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def validate_database(path: Path | str) -> list[str]:
    """Validate GparatypeDB directory. Return empty list if OK."""
    root = Path(path)
    errors: list[str] = []
    required = [
        "VERSION.txt",
        "db_manifest.tsv",
        "canonical_serovars.tsv",
        "howell_cds_components.tsv",
        "howell_cds_all.fasta",
        "canonical_architectures_long.tsv",
        "gene_aliases.tsv",
        "diagnostic_targets.tsv",
        "special_cases.tsv",
        "provenance.json",
        "checksums.sha256",
        "serovar_evidence_modes.tsv",
        "result_state_specification.tsv",
    ]
    for name in required:
        if not (root / name).is_file():
            errors.append(f"missing_required_file:{name}")

    if errors:
        return errors

    version = (root / "VERSION.txt").read_text(encoding="utf-8").strip()
    accepted_versions = {"GparatypeDB-2026.1-dev", "GparatypeDB-2026.1-freeze"}
    if (root / "VERSION_FREEZE.txt").is_file():
        freeze_label = (root / "VERSION_FREEZE.txt").read_text(encoding="utf-8").splitlines()[0].strip()
        if freeze_label:
            accepted_versions.add(freeze_label)
    if version not in accepted_versions:
        errors.append(f"unexpected_db_version:{version}")

    serovars = _read_tsv(root / "canonical_serovars.tsv")
    if len(serovars) != 15:
        errors.append(f"canonical_serovars_count:{len(serovars)}!=15")
    sero_ids = sorted(int(r["serovar"]) for r in serovars)
    if sero_ids != list(range(1, 16)):
        errors.append(f"canonical_serovar_ids:{sero_ids}")

    comps = _read_tsv(root / "howell_cds_components.tsv")
    if len(comps) != 253:
        errors.append(f"howell_cds_components_count:{len(comps)}!=253")

    ids = [r["component_id"] for r in comps]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_component_ids")

    for r in comps:
        if not r.get("accession"):
            errors.append(f"missing_accession:{r.get('component_id')}")
        if not r.get("sequence_sha256"):
            errors.append(f"missing_sequence_checksum:{r.get('component_id')}")
        if not r.get("source_publication") and not r.get("doi"):
            errors.append(f"missing_provenance:{r.get('component_id')}")

    # gene-order / adjacency internal validity
    by_sero: dict[int, list[dict[str, str]]] = {}
    for r in comps:
        by_sero.setdefault(int(r["serovar"]), []).append(r)
    for s, rows in by_sero.items():
        rows_sorted = sorted(rows, key=lambda x: int(x["gene_order"]))
        orders = [int(x["gene_order"]) for x in rows_sorted]
        if orders != list(range(1, len(orders) + 1)):
            errors.append(f"gene_order_gap_serovar_{s}:{orders}")
        for i, row in enumerate(rows_sorted):
            up = (row.get("upstream_neighbor") or "").strip()
            down = (row.get("downstream_neighbor") or "").strip()
            if i > 0 and up and up not in ("", "NONE"):
                prev = rows_sorted[i - 1]["gene_name"]
                if up != prev:
                    errors.append(
                        f"upstream_mismatch_s{s}_{row['accession']}:expected_{prev}_got_{up}"
                    )
            if i < len(rows_sorted) - 1 and down and down not in ("", "NONE"):
                nxt = rows_sorted[i + 1]["gene_name"]
                if down != nxt:
                    errors.append(
                        f"downstream_mismatch_s{s}_{row['accession']}:expected_{nxt}_got_{down}"
                    )

    special = _read_tsv(root / "special_cases.tsv")
    linked = False
    for row in special:
        if row.get("case_id") == "SPECIAL_CASE_5_12":
            seros = {int(x) for x in row.get("serovars", "").replace(";", ",").split(",") if x.strip()}
            if seros == {5, 12}:
                linked = True
    if not linked:
        errors.append("special_case_5_12_not_linked")

    # fasta count
    fasta = root / "howell_cds_all.fasta"
    n_seq = sum(1 for line in fasta.read_text(encoding="utf-8").splitlines() if line.startswith(">"))
    if n_seq != 253:
        errors.append(f"fasta_sequence_count:{n_seq}!=253")

    # checksums file present and covers key files
    chk = (root / "checksums.sha256").read_text(encoding="utf-8")
    if "howell_cds_all.fasta" not in chk or "howell_cds_components.tsv" not in chk:
        errors.append("checksums_incomplete")

    # verify listed checksums
    for line in chk.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        digest, rel = parts[0], parts[-1]
        fp = root / rel
        if not fp.is_file():
            errors.append(f"checksum_missing_file:{rel}")
            continue
        got = _sha256_file(fp)
        if got != digest:
            errors.append(f"checksum_mismatch:{rel}")

    return errors


def load_database(path: Path | str | None = None) -> GparatypeDatabase:
    from gparatype.utils import project_root

    if path is None:
        path = default_database_path()
    root = Path(path)
    errs = validate_database(root)
    if errs:
        raise ValueError(f"GparatypeDB validation failed: {errs}")

    version = (root / "VERSION.txt").read_text(encoding="utf-8").strip()
    if (root / "VERSION_FREEZE.txt").is_file():
        freeze_label = (root / "VERSION_FREEZE.txt").read_text(encoding="utf-8").splitlines()[0].strip()
        if freeze_label:
            version = freeze_label
    checksum_of_manifest = _sha256_file(root / "checksums.sha256")

    db = GparatypeDatabase(
        path=root,
        version=version,
        checksum_manifest_sha256=checksum_of_manifest,
        fasta_path=root / "howell_cds_all.fasta",
    )

    for row in _read_tsv(root / "canonical_serovars.tsv"):
        s = int(row["serovar"])
        db.serovars[s] = SerovarRecord(
            serovar=s,
            strain=row.get("strain", ""),
            aliases=row.get("aliases", ""),
            special_case=row.get("special_case", ""),
            evidence_mode=row.get("evidence_mode", ""),
            readiness=row.get("readiness", ""),
        )

    for row in _read_tsv(root / "howell_cds_components.tsv"):
        rec = ComponentRecord(
            component_id=row["component_id"],
            serovar=int(row["serovar"]),
            reference_strain=row.get("reference_strain", ""),
            gene_name=row["gene_name"],
            aliases=row.get("aliases", ""),
            accession=row["accession"],
            gene_order=int(row["gene_order"]),
            orientation=row.get("orientation", ""),
            sequence_length=int(row.get("sequence_length") or 0),
            upstream_neighbor=row.get("upstream_neighbor", ""),
            downstream_neighbor=row.get("downstream_neighbor", ""),
            source_publication=row.get("source_publication", ""),
            doi=row.get("doi", ""),
            local_fasta=row.get("local_fasta", ""),
            sequence_sha256=row.get("sequence_sha256", ""),
            notes=row.get("notes", ""),
        )
        db.components.append(rec)
        db.components_by_accession[rec.accession] = rec
        db.components_by_serovar.setdefault(rec.serovar, []).append(rec)

    db.architectures_long = _read_tsv(root / "canonical_architectures_long.tsv")
    db.gene_aliases = _read_tsv(root / "gene_aliases.tsv")

    for row in _read_tsv(root / "diagnostic_targets.tsv"):
        s = int(row["serovar"])
        db.diagnostic_targets[s] = DiagnosticTarget(
            serovar=s,
            gene=row["gene"],
            accession=row["accession"],
            aliases=row.get("aliases", ""),
            source=row.get("source", ""),
            notes=row.get("notes", ""),
        )

    for row in _read_tsv(root / "special_cases.tsv"):
        seros = [
            int(x.strip())
            for x in row.get("serovars", "").replace(";", ",").split(",")
            if x.strip()
        ]
        db.special_cases.append(
            SpecialCase(
                case_id=row["case_id"],
                serovars=seros,
                description=row.get("description", ""),
                rule=row.get("rule", ""),
            )
        )

    for row in _read_tsv(root / "serovar_evidence_modes.tsv"):
        s = int(row["serovar"])
        db.modes[s] = row

    db.result_states = _read_tsv(root / "result_state_specification.tsv")
    db.provenance = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
    return db


def _package_bundled_database_path() -> Path:
    """GparatypeDB directory shipped inside the installed gparatype package."""
    return Path(__file__).resolve().parent.parent / "data" / "GparatypeDB-2026.1-freeze"


def default_database_path() -> Path:
    from gparatype.utils import project_root

    bundled = _package_bundled_database_path()
    if bundled.is_dir() and (bundled / "checksums.sha256").is_file():
        return bundled

    return project_root() / "data" / "gparatype_db" / "GparatypeDB-2026.1-freeze"
