"""Unit tests for Gparatype v0.2 database load/validate (freeze DB)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gparatype.utils import project_root
from gparatype.v02.database import default_database_path, load_database, validate_database

ROOT = project_root()
DB = ROOT / "data" / "gparatype_db" / "GparatypeDB-2026.1-freeze"


@pytest.mark.skipif(not DB.is_dir(), reason="GparatypeDB-2026.1-freeze not present")
def test_validate_database_ok():
    errs = validate_database(DB)
    assert errs == []


@pytest.mark.skipif(not DB.is_dir(), reason="GparatypeDB-2026.1-freeze not present")
def test_load_database_15_serovars_253_components():
    db = load_database(DB)
    assert db.version == "GparatypeDB-2026.1-freeze"
    assert len(db.serovars) == 15
    assert len(db.components) == 253
    assert len(db.diagnostic_targets) == 15
    special = [s for s in db.special_cases if s.case_id == "SPECIAL_CASE_5_12"]
    assert special and set(special[0].serovars) == {5, 12}
    ids = [c.component_id for c in db.components]
    assert len(ids) == len(set(ids))


def test_default_path_points_to_freeze():
    assert default_database_path().name == "GparatypeDB-2026.1-freeze"
