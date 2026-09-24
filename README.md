
# Gparatype

**Architecture-aware genomic interpretation of capsule-associated diversity in** ***Glaesserella parasuis***

**Version:** 0.2.1 · **Default engine:** 0.2.1 (hybrid) · **Database:** GparatypeDB-2026.1-freeze

**Research-use notice:** Gparatype v0.2.1 is a research-use prototype that has not undergone independent external validation. Results should not be used as a standalone veterinary diagnostic or clinical decision-making tool.

## Overview

Gparatype is a bioinformatics framework for interpreting serovar-associated capsule genomic architectures in *Glaesserella parasuis*, the causative agent of Glässer's disease in swine. It analyzes whole-genome **assembly FASTA** files against curated Howell capsule-locus references. Raw sequencing reads (FASTQ) are not accepted as input.

Rather than relying on a single capsule marker, Gparatype integrates diagnostic-region sequence evidence, capsule-associated gene content, local gene order and genomic neighborhood, competing-serovar evidence, and assembly completeness and sequence-coverage signals. Its hybrid evidence framework reports uncertainty when evidence is incomplete or conflicting instead of forcing a numbered serovar assignment.

### Biological interpretation

Gparatype's primary typing unit is the **serovar-associated genomic capsule architecture**. A computational architecture interpretation is not necessarily equivalent to phenotypic serovar identity. The current version does not claim reliable discrimination of all 15 classical serovars:

- Serovars **5 and 12** are reported together as `SEROVAR_5_OR_12`.
- Serovars **2, 8 and 10** remain biologically unresolved at population scale.
- Insufficient, atypical or conflicting genomic evidence may produce an explicit ambiguity or limitation state.

## Installation

### Requirements

- Python **3.9 or newer**
- NCBI BLAST+, with `blastn` available on your `PATH` (installed separately)

### Install from PyPI

```bash
pip install gparatype
```

Verify the installation:

```bash
gparatype --version
gparatype --help
blastn -version
```

The Python package includes the `GparatypeDB-2026.1-freeze` research database; BLAST+ is an external requirement.

## Quick start

Run Gparatype on an assembled *G. parasuis* genome in FASTA format:

```bash
gparatype \
  --input assembly.fasta \
  --output-dir results/example_run
```

The default engine is `0.2.1`; specifying `--engine` is unnecessary for standard use. An alternative compatible database can be provided with `--database /path/to/database`.

### Main command-line options

| Option | Description |
|---|---|
| `--input`, `-i` | **Required:** whole-genome assembly in FASTA format |
| `--output-dir`, `-o` | Directory for output files |
| `--engine` | Analysis engine; default `0.2.1` |
| `--database` | Optional path to a compatible alternative database |
| `--reported-serovar` | Optional reporting metadata; does **not** influence the prediction |
| `--keep-blast` | Retain intermediate BLAST TSV output |
| `--verbose`, `-v` | Show additional processing information |

Earlier engines (`0.2` and `0.1.1`) remain available for reproducibility of previous analyses; see reproducibility documentation.

## Output

Gparatype writes the following files to the selected output directory:

| File | Description |
|---|---|
| `<sample>.gparatype_v02.txt` | Human-readable analysis summary |
| `<sample>.gparatype_v02.json` | Machine-readable run payload |
| `summary.tsv` | One-row sample summary |
| `architecture_evidence.tsv` | Per-serovar architecture evidence |
| `component_evidence.tsv` | Component-level evidence |

The console also reports the result state, primary architecture interpretation and an interpretation message.

### Interpretation states

| State | Meaning |
|---|---|
| `SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE` | Evidence supports a serovar-associated capsule architecture |
| `SEROVAR_5_OR_12` | Evidence supports the shared genomic state associated with serovars 5 and 12 |
| `AMBIGUOUS_ARCHITECTURE` | Multiple interpretations remain plausible |
| `ATYPICAL_CAPSULE_PROFILE` | Genomic features do not cleanly match an expected architecture |
| `INSUFFICIENT_CAPSULE_SEQUENCE` | Capsule-locus sequence evidence is insufficient |
| `ASSEMBLY_LIMITED` | Assembly characteristics limit interpretation |
| `CONFLICTING_GENOMIC_EVIDENCE` | Genomic signals support competing interpretations |
| `NO_RECOGNIZED_CAPSULE_ARCHITECTURE` | No recognized capsule architecture identified |
| `SPECIES_CHECK_FAILED` | Input did not satisfy the expected species-level check |
| `ERROR` | Analysis could not be completed successfully |

These states distinguish supported genomic interpretations from unresolved or technically limited cases.

## Reference database

The default database is **GparatypeDB-2026.1-freeze**. It contains curated capsule-locus reference material used by the v0.2.1 research engine. The installed database is located under `gparatype/data/GparatypeDB-2026.1-freeze/`; a repository copy is maintained under `data/gparatype_db/GparatypeDB-2026.1-freeze/`.

Database `checksums.sha256` checksum marker:

```text
b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a
```

See [database documentation](docs/DATABASE.md) for composition, provenance and reference selection.

## Validation and limitations

Gparatype v0.2.1 has undergone **internal development evaluation** using a clean evaluation subset (**n = 315**). The development cohort includes data associated with framework development and must **not** be interpreted as an independent benchmark. Independent external and clinical validation have not yet been completed.

Interpretations may be affected by incomplete resolution of some serovar groups, fragmented assemblies, reference-database coverage and conflicting genomic evidence. The software is not intended to replace phenotypic serotyping, laboratory confirmation, established diagnostic workflows or independent epidemiological investigation.

Future evaluation should include independent datasets, geographically and epidemiologically distinct isolates, and additional laboratory-confirmed phenotypic information where available. See [limitations](docs/LIMITATIONS.md) for details.

## Reproducibility

Record these components when reporting analyses:

```text
Software version: 0.2.1
Engine:           0.2.1
Database:         GparatypeDB-2026.1-freeze
```

Large validation genome FASTA files are not distributed with this release. The repository contains software, the research database, documentation, examples and tests for reproducing the computational workflow when input data are independently available. For legacy-engine instructions and additional details, see [reproducibility documentation](docs/REPRODUCIBILITY.md).

## Citation

A manuscript describing Gparatype is in preparation. Until a DOI is assigned, please use the software citation metadata in [CITATION.cff](CITATION.cff), specifying the software version and database version used. This section will be updated when an archival software release or manuscript receives a DOI.

## References

- Howell KJ, Weinert LA, Luan S-L, et al. Gene content and diversity of the loci encoding biosynthesis of capsular polysaccharides of the 15 serovar reference strains of *Haemophilus parasuis*. *Journal of Bacteriology*. 2013;195(18):4264–4273. [https://doi.org/10.1128/JB.00471-13](https://doi.org/10.1128/JB.00471-13)

- Howell KJ, Peters SE, Wang J, et al. Development of a multiplex PCR assay for rapid molecular serotyping of *Haemophilus parasuis*. *Journal of Clinical Microbiology*. 2015;53(12):3812–3821. [https://doi.org/10.1128/JCM.01991-15](https://doi.org/10.1128/JCM.01991-15)

## Contributors and license

Gparatype was developed and is maintained by **Emmanuel Kuufire**. Scientific, technical, advisory and other contributions are acknowledged in [CONTRIBUTORS.md](CONTRIBUTORS.md).

Gparatype is distributed under the MIT License.

## Documentation

- [Limitations and validation](docs/LIMITATIONS.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Reference database](docs/DATABASE.md)
- [Examples](examples/README.md)

**Status:** Gparatype v0.2.1 is a research-use release under active evaluation. Independent validation is required to establish performance beyond the current development setting.
