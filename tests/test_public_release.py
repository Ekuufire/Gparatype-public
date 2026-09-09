"""Public distribution tests — freeze DB, version, project_root, interpretation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import gparatype
from gparatype.blast import blastn_available, run_blastn
from gparatype.utils import project_root, validate_nucleotide_fasta
from gparatype.v02.database import (
    _package_bundled_database_path,
    default_database_path,
    load_database,
    validate_database,
)
from gparatype.v02.hybrid_interpretation import interpret_profiles_hybrid
from gparatype.v02.interpretation import interpret_profiles
from gparatype.v02.models import ArchitectureEvidenceProfile, ArchitectureProfile, DiagnosticEvidence

EXPECTED_CHECKSUMS_SHA256 = "b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a"
PUBLIC_ROOT = Path(__file__).resolve().parents[1]
ROOT_DB = PUBLIC_ROOT / "data" / "gparatype_db" / "GparatypeDB-2026.1-freeze"
PKG_DB = _package_bundled_database_path()


def test_version_is_021():
    assert gparatype.__version__ == "0.2.1"


def test_project_root_finds_public_tree():
    root = project_root()
    assert (root / "data" / "gparatype_db").is_dir()
    assert "Gparatype-public" in str(root) or root == PUBLIC_ROOT


def test_package_bundled_database_present_in_source_tree():
    assert PKG_DB.is_dir()
    assert (PKG_DB / "checksums.sha256").is_file()


def test_default_database_is_freeze():
    db_path = default_database_path()
    assert db_path.name == "GparatypeDB-2026.1-freeze"
    assert db_path.is_dir()
    assert "-dev" not in db_path.name
    assert (db_path / "checksums.sha256").is_file()


def test_default_database_prefers_package_bundled():
    assert default_database_path() == PKG_DB


def test_both_checksums_sha256_files_match():
    root_chk = ROOT_DB / "checksums.sha256"
    pkg_chk = PKG_DB / "checksums.sha256"
    assert root_chk.is_file() and pkg_chk.is_file()
    for path in (root_chk, pkg_chk):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == EXPECTED_CHECKSUMS_SHA256
    assert root_chk.read_bytes() == pkg_chk.read_bytes()


def test_gparatype_source_tree_not_private_repo():
    pkg_path = Path(gparatype.__file__).resolve()
    path_str = str(pkg_path)
    if "site-packages" in path_str:
        assert "gparatype" in path_str
        db_path = default_database_path()
        norm = str(db_path).replace("\\", "/")
        assert "gparatype/data/GparatypeDB-2026.1-freeze" in norm
    else:
        assert "Gparatype-public" in path_str
        private_root = str(PUBLIC_ROOT).replace("Gparatype-public", "Gparatype")
        assert not path_str.startswith(private_root + "/")
        assert not path_str.startswith(private_root + "\\")


@pytest.mark.skipif(not ROOT_DB.is_dir(), reason="root freeze DB missing")
def test_validate_root_freeze_database_ok():
    assert validate_database(ROOT_DB) == []


@pytest.mark.skipif(not PKG_DB.is_dir(), reason="package freeze DB missing")
def test_validate_package_freeze_database_ok():
    assert validate_database(PKG_DB) == []


@pytest.mark.skipif(not PKG_DB.is_dir(), reason="package freeze DB missing")
def test_load_package_freeze_database():
    db = load_database(PKG_DB)
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
