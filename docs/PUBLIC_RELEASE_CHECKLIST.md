# Public release checklist (Gparatype 0.2.1-research)

Public distribution packaging checklist. **Do not** push or configure remotes
until human approval.

## Scientific freeze

- [x] Hybrid v0.2.1 research release only (no Phase analysis outputs)
- [x] GparatypeDB-2026.1-freeze bundled (not `-dev`)
- [x] Default `default_database_path()` → `-freeze`
- [x] DB checksum marker verified (`b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a`)

## Documentation

- [x] README (architecture-aware framework, FASTA not FASTQ, research disclaimer)
- [x] `docs/LIMITATIONS.md` (Phase 5F CLEAN metrics)
- [x] `docs/REPRODUCIBILITY.md`
- [x] `docs/DATABASE.md`
- [x] `docs/LICENSE_DECISION_REQUIRED.md` (no invented LICENSE)
- [x] `CITATION.cff` (no invented DOI)
- [x] `examples/README.md` (accession-based; no fabricated serovar)

## Installability / tests

- [x] Fresh venv install verified (`pip install -e .[dev]` in `/tmp/gparatype-public-test-venv`)
- [x] Fresh venv **non-editable** install verified (`pip install /home/labstudent/Gparatype-public` from `/tmp`; `default_database_path()` resolves to `site-packages/gparatype/data/GparatypeDB-2026.1-freeze`)
- [x] `gparatype --help` / `--version` OK
- [x] `pytest` passes (17 passed, 1 skipped)
- [x] `gparatype.__file__` under Gparatype-public (not private repo)

## Safety audits

- [x] Secrets audit (public tree only; no obvious patterns in code/docs)
- [x] Large-file audit: total ~1.2 MB tracked; largest file ~274 KB (`howell_cds_all.fasta`); none >10 MB
- [x] Private `.git` untouched (HEAD `b682f525` before/after)

## License / governance — PUBLIC_RELEASE_BLOCKER

- [ ] **License approved** and `LICENSE` committed  
  Until then: [LICENSE_DECISION_REQUIRED.md](LICENSE_DECISION_REQUIRED.md)  
  **PUBLIC_RELEASE_BLOCKER:** license

## GitHub / visibility (STOP)

- [ ] Remote configured (human only)
- [ ] Push authorized (human only)
- [x] This packaging pass does **not** push or configure remote

## Git state (public)

- [x] Fresh repo initialized in `Gparatype-public` only
- [x] Initial commit: `Initial public research release of Gparatype v0.2.1` (`5c9b2c34`)
- [x] Bundle commit: `Bundle GparatypeDB-2026.1-freeze in package data for pip install` (`942268d`)
- [x] 77 tracked files; working tree clean
