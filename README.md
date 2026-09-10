# Gparatype

**Architecture-aware genomic interpretation of capsule-associated diversity in *Glaesserella parasuis***

**Research prototype:** Gparatype v0.2.1
**Software package version:** `0.2.1`(hybrid; default)
**Default database:** `GparatypeDB-2026.1-freeze`

> **Research-use notice:** Gparatype v0.2.1 is a research-use prototype and has not undergone independent external validation. Results should not be used as a standalone veterinary diagnostic or clinical decision-making tool.

See also: [docs/LIMITATIONS.md](docs/LIMITATIONS.md), [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md), [docs/DATABASE.md](docs/DATABASE.md), [docs/PUBLIC_RELEASE_CHECKLIST.md](docs/PUBLIC_RELEASE_CHECKLIST.md), [docs/LICENSE_DECISION_REQUIRED.md](docs/LICENSE_DECISION_REQUIRED.md), and [examples/README.md](examples/README.md).

---

## Overview

Gparatype is an architecture-aware bioinformatics framework for genome-based interpretation of serovar-associated capsule architectures in *Glaesserella parasuis*.

The framework analyzes **whole-genome assembly FASTA files** against curated Howell capsule-locus references. The input is a nucleotide assembly in **FASTA format**, not raw sequencing reads in FASTQ format.

Rather than relying on a single capsule marker, Gparatype integrates multiple genomic signals, including:

* diagnostic-region sequence evidence;
* capsule-associated gene content;
* local gene order and genomic neighborhood;
* competing-serovar evidence;
* assembly completeness and sequence-coverage signals.

The default `0.2.1` engine uses a hybrid evidence framework designed to favor conservative interpretations when genomic evidence is incomplete, conflicting, or insufficient for a confident assignment.

### Biological interpretation

The primary typing unit used by Gparatype is a **serovar-associated genomic capsule architecture**. This represents a computational interpretation of capsule-locus evidence and should not automatically be considered equivalent to phenotypic serovar identity.

Gparatype does **not** claim reliable discrimination of all 15 classical *G. parasuis* serovars.

In particular:

* Serovars **5 and 12** are reported as the combined state `SEROVAR_5_OR_12`.
* Serovars **2, 8, and 10** remain biologically unresolved at population scale.
* Samples with insufficient, atypical, or conflicting genomic evidence may receive an ambiguity or limitation state rather than an unsupported numbered assignment.

This conservative behavior is intentional: **uncertain genomic evidence is reported as uncertain rather than forced into a serovar label.**

---

## Installation

### Requirements

* Python ≥ 3.9
* NCBI BLAST+ with `blastn` available on `PATH`

### Recommended installation

Clone the repository and install from the checkout root:

```bash
git clone <repo-url> Gparatype-public
cd Gparatype-public

pip install ".[dev]"
```

For development:

```bash
pip install -e ".[dev]"
```

The standard package installation includes the bundled research database:

```text
GparatypeDB-2026.1-freeze
```

The database is installed with the package under:

```text
gparatype/data/GparatypeDB-2026.1-freeze/
```

For transparency and clone-and-run reproducibility, the same database is maintained in the repository under:

```text
data/gparatype_db/GparatypeDB-2026.1-freeze/
```

Gparatype resolves the package-bundled database first and then the repository copy.

A different compatible database can be supplied explicitly with:

```bash
--database /path/to/GparatypeDB-2026.1-freeze
```

### Optional conda environment

An environment specification is provided in `environment.yml`:

```bash
conda env create -f environment.yml
conda activate gparatype
pip install -e ".[dev]"
```

---

## Quick start

Check the installation:

```bash
gparatype --help
gparatype --version
```

Run Gparatype on a whole-genome assembly:

```bash
gparatype \
  --input <assembly.fasta> \
  --output-dir results/example_run
```

The command above uses the **Gparatype v0.2.1** hybrid engine by default. The --engine option is therefore not required for the standard workflow.

The equivalent explicit command is:
```bash
gparatype \
  --input <assembly.fasta> \
  --engine 0.2.1 \
  --output-dir results/example_run
```

For routine use, the shorter command is recommended.

Engine selection

**Gparatype v0.2.1** is the default and recommended engine for the current public release.

Previous engines are retained for reproducibility of earlier analyses.

**v0.2.1 — Hybrid engine**

Default:
```bash
gparatype \
  --input <assembly.fasta> \
  --output-dir results/example_run
```

Explicit selection:
```bash
gparatype \
  --input <assembly.fasta> \
  --engine 0.2.1 \
  --output-dir results/example_run
  ```
v0.2 — Phase 5A

The v0.2 engine is retained as a frozen legacy workflow:
```bash
gparatype \
  --input <assembly.fasta> \
  --engine 0.2 \
  --output-dir results/phase5a_example
```
v0.1.1 — Baseline

The v0.1.1 baseline engine is retained for reproducibility:
```bash
gparatype \
  --input <assembly.fasta> \
  --engine 0.1.1 \
  --output-dir results/baseline_example
```

Legacy engines should generally be used when reproducing or comparing earlier analyses rather than for new routine analyses.

Python module invocation

Gparatype can also be invoked as a Python module:

python -m gparatype

The installed gparatype command is the recommended interface for normal use.

### Command-line options

| Flag                  | Description                                                        |
| --------------------- | ------------------------------------------------------------------ |
| `--input` / `-i`      | **Required.** Whole-genome assembly in FASTA format                |
| `--engine`            | Analysis engine. Default: `0.2.1`                                  |
| `--database`          | Optional path to an alternative Gparatype database                 |
| `--output-dir` / `-o` | Directory for analysis outputs                                     |
| `--reported-serovar`  | Optional metadata for reporting; does **not** influence prediction |
| `--keep-blast`        | Retain intermediate BLAST TSV output                               |
| `--verbose` / `-v`    | Print additional paths and processing information                  |

Legacy engines (`0.2` and `0.1.1`) are retained for reproducibility of earlier analyses.

---

## Output

Gparatype writes results to the specified output directory.

| File                          | Description                       |
| ----------------------------- | --------------------------------- |
| `<sample>.gparatype_v02.txt`  | Human-readable analysis summary   |
| `<sample>.gparatype_v02.json` | Machine-readable run payload      |
| `summary.tsv`                 | One-row sample summary            |
| `architecture_evidence.tsv`   | Per-serovar architecture evidence |
| `component_evidence.tsv`      | Component-level evidence          |

The console reports the final result state, primary architecture interpretation, and a corresponding interpretation message.

---

## Result states

The v0.2.1 engine reports one of the following result states:

| Result state                                | General interpretation                                                            |
| ------------------------------------------- | --------------------------------------------------------------------------------- |
| `SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE` | Genomic evidence supports a serovar-associated capsule architecture               |
| `SEROVAR_5_OR_12`                           | Evidence supports the shared genomic state associated with serovars 5 and 12      |
| `AMBIGUOUS_ARCHITECTURE`                    | Multiple interpretations remain plausible                                         |
| `ATYPICAL_CAPSULE_PROFILE`                  | Capsule-associated genomic features do not match an expected architecture cleanly |
| `INSUFFICIENT_CAPSULE_SEQUENCE`             | Available sequence does not provide sufficient capsule-locus evidence             |
| `ASSEMBLY_LIMITED`                          | Assembly characteristics limit interpretation                                     |
| `CONFLICTING_GENOMIC_EVIDENCE`              | Genomic signals support competing interpretations                                 |
| `NO_RECOGNIZED_CAPSULE_ARCHITECTURE`        | No recognized capsule architecture was identified                                 |
| `SPECIES_CHECK_FAILED`                      | Input did not satisfy the expected species-level check                            |
| `ERROR`                                     | Analysis could not be completed successfully                                      |

These states are intended to distinguish **supported genomic interpretations from unresolved or technically limited cases**.

---

## Database

The default research database is:

```text
GparatypeDB-2026.1-freeze
```

Repository location:

```text
data/gparatype_db/GparatypeDB-2026.1-freeze/
```

The database contains the curated capsule-locus reference material used by the Gparatype v0.2.1 research engine.

The checksum marker for the database `checksums.sha256` file is:

```text
b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a
```

Database composition, provenance, reference selection, and reproducibility information are described in [docs/DATABASE.md](docs/DATABASE.md).

---

## Validation and development status

Gparatype v0.2.1 has undergone **internal development evaluation** but has **not yet undergone independent external validation**.

Current validation status:

* **External validation:** Not performed
* **Clinical validation:** Not performed
* **Development evaluation:** Internal comparison using a clean evaluation subset (`n=315`)
* **Development cohort:** Contains data associated with framework development and should therefore not be interpreted as an independent benchmark

Development results are intended to assess framework behavior and identify areas requiring further evaluation. They should **not** be presented as independent external validation or clinical performance estimates.

Future evaluation should include independent datasets, geographically and epidemiologically distinct isolates, and additional laboratory-confirmed phenotypic information where available.

For the detailed validation framework and limitations, see [docs/LIMITATIONS.md](docs/LIMITATIONS.md) and [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

---

## Reproducibility

For reproducible analyses, record and retain:

```text
Software version: 0.2.1
Engine:           0.2.1
Database:         GparatypeDB-2026.1-freeze
```

Large validation genome FASTA files are **not distributed with this public release**.

The public repository provides the software, research database, documentation, examples, and tests necessary to understand and reproduce the computational workflow where the corresponding input data are independently available.

See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) for additional information.

---

## Research use and limitations

Gparatype is intended to support **research into genomic diversity, capsule architecture, and serovar-associated variation in *G. parasuis*.**

It is not currently intended to replace:

* phenotypic serotyping;
* laboratory confirmation;
* established diagnostic workflows;
* epidemiological investigation based on independent evidence.

The framework should be interpreted in the context of its reference database, assembly quality, genomic diversity, and current validation status.

Important limitations include incomplete resolution of certain serovar groups, potential effects of assembly fragmentation, database dependence, and the absence of independent external and clinical validation.

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the complete limitations statement.

---

## Citation

A manuscript describing Gparatype is in preparation.

For software citation, please use the information provided in [CITATION.cff](CITATION.cff).

**No DOI is currently assigned.**

Once a manuscript or archival software release receives a DOI, the citation information will be updated accordingly.

---

## License

The license for the public software release is currently **under consideration**.

No `LICENSE` file is included in this release until the appropriate licensing decision has been finalized.

See [docs/LICENSE_DECISION_REQUIRED.md](docs/LICENSE_DECISION_REQUIRED.md).

---

## Project structure

```text
Gparatype-public/
├── src/gparatype/             # Gparatype v0.2.1 engine and legacy paths
├── data/gparatype_db/         # GparatypeDB-2026.1-freeze
├── docs/                      # Documentation and release information
├── examples/                  # Usage examples and guidance
├── tests/                     # Public installation and software tests
├── pyproject.toml
└── CITATION.cff
```

---

## Status

**Gparatype v0.2.1 is a research prototype under continued development and evaluation.**

The current release provides an architecture-aware computational framework for interpreting capsule-associated genomic diversity in *Glaesserella parasuis*, while explicitly reporting unresolved and technically limited cases.

Independent validation and further refinement are required before the framework can be considered for diagnostic or clinical use.
