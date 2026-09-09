"""Public distribution tests — freeze DB, version, project_root, interpretation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import gparatype
from gparatype.blast import blastn_available, run_blastn
from gparatype.utils import project_root, validate_nucleotide_fasta
from gparatype.v02.database import default_database_path, load_database, validate_database
from gparatype.v02.hybrid_interpretation import interpret_profiles_hybrid
from gparatype.v02.interpretation import interpret_profiles
from gparatype.v02.models import ArchitectureEvidenceProfile, ArchitectureProfile, DiagnosticEvidence

EXPECTED_CHECKSUMS_SHA256 = "b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a"
PUBLIC_ROOT = Path(__file__).resolve().parents[1]
DB = PUBLIC_ROOT / "data" / "gparatype_db" / "GparatypeDB-2026.1-freeze"


def test_version_is_021():
    assert gparatype.__version__ == "0.2.1"


def test_project_root_finds_public_tree():
    root = project_root()
    assert (root / "data" / "gparatype_db").is_dir()
    assert "Gparatype-public" in str(root) or root == PUBLIC_ROOT


def test_default_database_is_freeze():
    db_path = default_database_path()
    assert db_path.name == "GparatypeDB-2026.1-freeze"
    assert db_path.is_dir()
    assert "-dev" not in db_path.name


def test_gparatype_installed_from_public_tree():
    pkg_path = Path(gparatype.__file__).resolve()
    path_str = str(pkg_path)
    assert "Gparatype-public" in path_str
    private_root = str(PUBLIC_ROOT).replace("Gparatype-public", "Gparatype")
    assert not path_str.startswith(private_root + "/")
    assert not path_str.startswith(private_root + "\\")


def test_freeze_checksum_marker():
    chk = DB / "checksums.sha256"
    assert chk.is_file()
    digest = hashlib.sha256(chk.read_bytes()).hexdigest()
    assert digest == EXPECTED_CHECKSUMS_SHA256


@pytest.mark.skipif(not DB.is_dir(), reason="freeze DB missing")
def test_validate_freeze_database_ok():
    assert validate_database(DB) == []


@pytest.mark.skipif(not DB.is_dir(), reason="freeze DB missing")
def test_load_freeze_database():
    db = load_database(DB)
    assert db.version == "GparatypeDB-2026.1-freeze"
    assert len(db.serovars) == 15
    assert len(db.components) == 253
    assert db.checksum_manifest_sha256 == EXPECTED_CHECKSUMS_SHA256


def _prof(
    serovar: int,
    recovery: float,
    *,
    mode: str = "HYBRID_TARGET_ARCHITECTURE",
    content: str = "MODERATE",
    diag: str = "MODERATE",
) -> ArchitectureEvidenceProfile:
    arch = ArchitectureProfile(
        serovar=serovar,
        reference_strain="ref",
        n_expected=15,
        n_present=10,
        n_partial=0,
        n_not_detected=5,
        n_not_observable=0,
        recovery_fraction=recovery,
        order_status="ORDER_AGREE",
        adjacency_status="ADJACENCY_AGREE",
        orientation_status="ORIENTATION_AGREE",
        assembly_limited=False,
        components=[],
    )
    return ArchitectureEvidenceProfile(
        serovar=serovar,
        reference_strain="ref",
        evidence_mode=mode,
        readiness="PROVISIONAL",
        content_evidence=content,
        sequence_evidence="STRONG",
        order_evidence="STRONG",
        adjacency_evidence="STRONG",
        orientation_evidence="MODERATE",
        diagnostic_evidence=diag,
        completeness_evidence="MODERATE",
        assembly_limitations="NOT_ASSESSABLE",
        competing_evidence="WEAK",
        recovery_fraction=recovery,
        warnings=[],
        architecture=arch,
        diagnostic=DiagnosticEvidence(serovar, "g", "A", diag),
    )


def test_phase5a_competing_ambiguous():
    profiles = [
        _prof(8, 0.70, mode="SINGLE_TARGET_WITH_ARCHITECTURE_CONFIRMATION", content="STRONG", diag="STRONG"),
        _prof(10, 0.68, mode="HYBRID_TARGET_ARCHITECTURE", content="STRONG"),
    ] + [_prof(s, 0.1, content="WEAK", diag="NOT_ASSESSABLE") for s in range(1, 16) if s not in (8, 10)]
    by = {p.serovar: p for p in profiles}
    profiles = [by[s] for s in range(1, 16)]
    res = interpret_profiles(profiles, species_status="SPECIES_OK", capsule_detected=True)
    assert res.final_state == "AMBIGUOUS_ARCHITECTURE"


def test_hybrid_5_12_special_case():
    profiles = []
    for s in range(1, 16):
        if s in (5, 12):
            profiles.append(
                _prof(s, 0.85, mode="SPECIAL_CASE_5_12", content="STRONG", diag="STRONG")
            )
        else:
            profiles.append(_prof(s, 0.1, content="WEAK", diag="NOT_ASSESSABLE"))
    res = interpret_profiles_hybrid(profiles, species_status="SPECIES_OK", capsule_detected=True)
    assert res.final_state == "SEROVAR_5_OR_12"


def test_fasta_validation(tmp_path):
    p = tmp_path / "ok.fa"
    p.write_text(">c1\nATGCATGC\n", encoding="utf-8")
    info = validate_nucleotide_fasta(p)
    assert info["n_records"] == 1


def test_blastn_missing_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr("gparatype.blast.blastn_available", lambda: False)
    q = tmp_path / "q.fa"
    s = tmp_path / "s.fa"
    q.write_text(">q\nATGC\n", encoding="utf-8")
    s.write_text(">s\nATGC\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="blastn"):
        run_blastn(q, s)


@pytest.mark.skipif(blastn_available(), reason="blastn present")
def test_blastn_not_on_path_skipped_integration():
    assert blastn_available() is False
