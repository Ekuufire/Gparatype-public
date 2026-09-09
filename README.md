# Gparatype

Gparatype is an architecture-aware bioinformatics framework for genome-based interpretation of serovar-associated capsule architectures in *Glaesserella parasuis*.

**Research designation:** Gparatype **0.2.1-research**  
**Software package version:** `0.2.1`  
**Default database:** `GparatypeDB-2026.1-freeze`  
**Phase 5F decision:** `PROMISING_BUT_NEEDS_REFINEMENT`

> **Gparatype v0.2.1-research is a research-use prototype and has not undergone independent external validation. Results should not be used as a standalone veterinary diagnostic or clinical decision-making tool.**

See also: [docs/LIMITATIONS.md](docs/LIMITATIONS.md), [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md), [docs/DATABASE.md](docs/DATABASE.md), [docs/PUBLIC_RELEASE_CHECKLIST.md](docs/PUBLIC_RELEASE_CHECKLIST.md), [docs/LICENSE_DECISION_REQUIRED.md](docs/LICENSE_DECISION_REQUIRED.md), [examples/README.md](examples/README.md).

## Overview

Gparatype interprets **whole-genome assembly FASTA** (nucleotide contigs or scaffolds) of *G. parasuis* against curated Howell capsule-locus references. Input must be **FASTA, not FASTQ**. The biological typing unit is a **serovar-associated genomic capsule architecture** — a computational interpretation of capsule-locus evidence — and is **not** automatically equivalent to phenotypic serovar identity.

The default CLI engine is the **hybrid 0.2.1** research prototype. It integrates diagnostic-region evidence, capsule gene content, local architecture (order / neighborhood), competing-serovar context, and assembly completeness signals. Conservative result states prefer ambiguity (`AMBIGUOUS_ARCHITECTURE`, `ASSEMBLY_LIMITED`) over unsupported numbered calls.

Gparatype does **not** claim reliable distinction of all 15 classical serovars. Serovars **5 and 12** are emitted only as the combined state **`SEROVAR_5_OR_12`**. Serovars **2, 8, and 10** remain biologically unresolved at population scale.

## Installation

Requires Python ≥3.9 and **NCBI BLAST+** (`blastn` on `PATH`).

```bash
pip install .
# or editable: pip install -e ".[dev]"
```

Optional conda environment (see `environment.yml`):

```bash
conda env create -f environment.yml
conda activate gparatype
pip install -e ".[dev]"
```

## Quick start

```bash
gparatype --help
gparatype --version
```

```bash
gparatype --input <assembly.fasta> \
  --engine 0.2.1 \
  --output-dir results/example_run
```

| Flag | Role |
|---|---|
| `--input` / `-i` | **Required.** Whole-genome assembly FASTA (not FASTQ) |
| `--engine` | Default `0.2.1` (hybrid). Legacy `0.2` / `0.1.1` for reproducibility only |
| `--database` | Override GparatypeDB path (default: bundled `GparatypeDB-2026.1-freeze`) |
| `--output-dir` / `-o` | Output directory for reports |
| `--reported-serovar` | Optional metadata for reporting only — **must not** influence prediction |
| `--keep-blast` | Retain BLAST TSV output |
| `--verbose` / `-v` | Log paths to stderr |

Also available: `python -m gparatype` with the same arguments.

## Output interpretation (engine 0.2.1)

Reports are written to `--output-dir`:

| File | Role |
|---|---|
| `<sample>.gparatype_v02.txt` | Human-readable summary |
| `<sample>.gparatype_v02.json` | Machine-readable run payload |
| `summary.tsv` | One-row summary |
| `architecture_evidence.tsv` | Per-serovar architecture evidence |
| `component_evidence.tsv` | Component-level evidence |

Console prints: `final_state`, primary architecture, and interpretation text.

**Result states** (`V02_RESULT_STATES`):

- `SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE`
- `SEROVAR_5_OR_12`
- `AMBIGUOUS_ARCHITECTURE`
- `ATYPICAL_CAPSULE_PROFILE`
- `INSUFFICIENT_CAPSULE_SEQUENCE`
- `ASSEMBLY_LIMITED`
- `CONFLICTING_GENOMIC_EVIDENCE`
- `NO_RECOGNIZED_CAPSULE_ARCHITECTURE`
- `SPECIES_CHECK_FAILED`
- `ERROR`

## Database

Bundled research-freeze database: `data/gparatype_db/GparatypeDB-2026.1-freeze/`

Checksum marker for `checksums.sha256` file: `b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a`

Details: [docs/DATABASE.md](docs/DATABASE.md)

## Validation status

- `EXTERNAL_VALIDATION=NOT_PERFORMED`
- `DEVELOPMENT_COHORT=DISCOVERY_CONTAMINATED`
- `CLINICAL_VALIDATION=NO`
- Phase 5F is an **INTERNAL_DEVELOPMENT_COMPARISON** only (`PROMISING_BUT_NEEDS_REFINEMENT`; CLEAN n=315)

Do not present development metrics as independent external validation. Full limitations: [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Reproducibility

Pin software `0.2.1`, engine `0.2.1`, and `GparatypeDB-2026.1-freeze`. Large validation genome FASTAs are **not** shipped with this public distribution. Details: [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Citation

Manuscript in preparation. Prefer [CITATION.cff](CITATION.cff). **No DOI is assigned.**

## License

License: **To be determined before public release.**

No `LICENSE` file is present. See [docs/LICENSE_DECISION_REQUIRED.md](docs/LICENSE_DECISION_REQUIRED.md).

## Project layout

```
Gparatype-public/
├── src/gparatype/             # hybrid 0.2.1 engine (+ legacy paths)
├── data/gparatype_db/         # GparatypeDB-2026.1-freeze only
├── docs/                      # release documentation
├── examples/                  # usage notes (no redistributable genomes)
├── tests/                     # public installability tests
├── pyproject.toml
└── CITATION.cff
```
