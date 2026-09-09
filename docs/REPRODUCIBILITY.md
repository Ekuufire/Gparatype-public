# Reproducibility (Gparatype 0.2.1-research)

Checkpoint for the architecture-aware hybrid research prototype public distribution.
Scientific calling rules and GparatypeDB biological content are **frozen**; do not retune
to “improve” metrics on the discovery cohort.

## Pin these identifiers

| Item | Value |
|---|---|
| Research label | `0.2.1-research` |
| Software `__version__` | `0.2.1` |
| Default CLI engine | `0.2.1` (hybrid) |
| Database directory | `data/gparatype_db/GparatypeDB-2026.1-freeze` |
| DB checksum marker (`checksums.sha256` file hash) | `b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a` |

Private development commit hashes (for manuscript cross-reference only; not shipped):

| Item | Value |
|---|---|
| Research-freeze tag | `v0.2.1-research-freeze` |
| Research-freeze commit | `cc72d103b396316ae7fbf9ebda06729647960e0c` |
| Hybrid implementation commit | `d42b5564d44a20f616223b3f908625636882ac56` |
| Phase 5F benchmark commit | `49c191d156ad0c3b114c4dfbad51cb6712ada90c` |

## Environment

- Python ≥3.9 (`pyproject.toml`)
- **BLAST+** (`blastn` on `PATH`) for live genome searches
- Install: `pip install .` or `pip install -e ".[dev]"`

```bash
python -m venv /tmp/gparatype-public-test-venv
source /tmp/gparatype-public-test-venv/bin/activate
pip install "/path/to/Gparatype-public[dev]"
gparatype --version
blastn -version
pytest
```

## Database

Public default: `default_database_path()` resolves to `GparatypeDB-2026.1-freeze`.

```bash
cd data/gparatype_db/GparatypeDB-2026.1-freeze
sha256sum checksums.sha256
grep b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a db_manifest.tsv
```

## Example run

```bash
gparatype --input <assembly.fasta> --engine 0.2.1 \
  --output-dir results/example_run
```

CLI flag is **`--database`** (not `--db`).

Expected outputs under `--output-dir`:

- `<sample>.gparatype_v02.txt`
- `<sample>.gparatype_v02.json`
- `summary.tsv`
- `architecture_evidence.tsv`
- `component_evidence.tsv`

Interpret states using [LIMITATIONS.md](LIMITATIONS.md) and `V02_RESULT_STATES`.

## Genomes not shipped

Whole-genome validation FASTAs are **not** included in this public tree. Obtain
public *G. parasuis* assemblies from NCBI (e.g. BioProject accessions cited in
Howell et al. and subsequent population studies) for independent testing.

Do **not** fabricate expected serovar calls when demonstrating on downloaded genomes
unless you have independent metadata.

## Tests

```bash
pytest
```

Public tests cover database loading, version pins, interpretation logic, and
install path independence — without requiring private validation genomes.
