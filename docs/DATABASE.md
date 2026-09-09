# GparatypeDB (public release)

## Bundled database

| Item | Value |
|---|---|
| Directory | `data/gparatype_db/GparatypeDB-2026.1-freeze/` |
| Freeze label | `GparatypeDB-2026.1-freeze` (see `VERSION_FREEZE.txt`) |
| Scientific content identity | Byte-identical to private `GparatypeDB-2026.1-dev` at Phase 5A freeze |
| `VERSION.txt` label | Still `GparatypeDB-2026.1-dev` (intentional; see `FREEZE_README.txt`) |
| Default in public code | `default_database_path()` → `-freeze` directory |

## Contents

| File | Role |
|---|---|
| `howell_cds_all.fasta` | 253 Howell CDS reference sequences |
| `howell_cds_components.tsv` | Component metadata (gene order, neighbors, checksums) |
| `canonical_serovars.tsv` | 15 canonical serovar records |
| `canonical_architectures_long.tsv` | Long-form architecture table |
| `diagnostic_targets.tsv` | Per-serovar diagnostic gene / accession |
| `serovar_evidence_modes.tsv` | Hybrid-engine evidence mode per serovar |
| `special_cases.tsv` | Special rules (e.g. combined 5/12) |
| `gene_aliases.tsv` | Gene alias table |
| `result_state_specification.tsv` | v0.2 result state definitions |
| `provenance.json` | Source publication / DOI metadata for components |
| `db_manifest.tsv` | File inventory with SHA256 hashes |
| `checksums.sha256` | Checksum manifest (see below) |
| `FREEZE_README.txt` | Freeze policy notes |
| `VERSION_FREEZE.txt` | Public freeze label |

## Checksum marker

The SHA256 hash **of the `checksums.sha256` file itself** (recorded in `db_manifest.tsv`):

```
b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a
```

Verify:

```bash
cd data/gparatype_db/GparatypeDB-2026.1-freeze
sha256sum checksums.sha256
grep b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a db_manifest.tsv
sha256sum -c checksums.sha256   # optional: verify all listed files
```

## Usage

Default (no flag needed after install):

```bash
gparatype --input assembly.fasta --engine 0.2.1 --output-dir results/run
```

Explicit override:

```bash
gparatype --input assembly.fasta \
  --database data/gparatype_db/GparatypeDB-2026.1-freeze \
  --output-dir results/run
```

## Not included

- `GparatypeDB-2026.1-dev` working copy (scientifically identical content; not shipped)
- Whole-genome validation cohorts
- Phase analysis outputs or curated signature tables from private development

## Modification policy

Do **not** edit scientific TSV/FASTA content in the freeze tree for threshold tuning or strain-specific logic. Treat this directory as read-only for reproducibility.
