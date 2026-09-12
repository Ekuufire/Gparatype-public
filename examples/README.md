# Gparatype Worked Examples

This directory provides worked examples demonstrating how to run and interpret **Gparatype v0.2.1**.

Gparatype reports **serovar-associated genomic capsule architectures**. These interpretations are based on genomic evidence and should not automatically be considered equivalent to phenotypic serovar identity.

> **Research-use notice:** Gparatype v0.2.1 is a research prototype and has not undergone independent external validation. Results should not be used as a standalone veterinary diagnostic or clinical decision-making tool.

---

## Example 1: Shared serovar 5/12-associated capsule architecture

### Genome

- **Organism:** *Glaesserella parasuis*
- **Strain:** KL0318
- **NCBI nucleotide accession:** `CP009237.1`
- **Gparatype engine:** `0.2.1`
- **Database:** `GparatypeDB-2026.1-freeze`

This example demonstrates how Gparatype handles a genome with strong evidence for the shared serovar 5/12-associated capsule architecture.

### Run Gparatype

After obtaining the corresponding genome assembly in FASTA format, run:

```bash
gparatype \
  --input CP009237.1.fasta \
  --output-dir results/KL0318
```

### Expected result

```text
final_state:          SEROVAR_5_OR_12
primary_architecture: 5_OR_12
competing_serovars:   5,12
species_status:       SPECIES_OK
capsule_detected:     True
```

### Architecture evidence

| Evidence | Serovar 5 | Serovar 12 |
|---|---:|---:|
| Architecture recovery | 1.000 | 1.000 |
| Gene content | STRONG | STRONG |
| Sequence evidence | STRONG | STRONG |
| Gene order | STRONG | STRONG |
| Adjacency | STRONG | STRONG |
| Diagnostic evidence | STRONG | STRONG |
| Completeness | STRONG | STRONG |
| Components detected | 14/14 | 14/14 |

Both serovar-associated reference architectures show complete recovery and strong genomic support.

### Interpretation

Despite the strength and completeness of the capsule-locus evidence, Gparatype does not force an individual serovar 5 or serovar 12 assignment.

Instead, it reports:

```text
SEROVAR_5_OR_12
```

This illustrates an important design principle of Gparatype:

> **When the available genomic evidence does not support a more specific interpretation, Gparatype reports the unresolved state rather than forcing an unsupported numbered assignment.**

The result represents a genomic capsule-architecture interpretation and should not be considered confirmation of phenotypic serovar identity.

---

## Example 2: Ambiguous architecture with competing genomic evidence

### Genome

- **Organism:** *Glaesserella parasuis*
- **Strain:** SC1401
- **NCBI nucleotide accession:** `CP015099.1`
- **Gparatype engine:** `0.2.1`
- **Database:** `GparatypeDB-2026.1-freeze`

This example demonstrates how Gparatype handles a genome for which a leading capsule architecture is accompanied by substantial competing genomic evidence.

### Run Gparatype

```bash
gparatype \
  --input CP015099.1.fasta \
  --output-dir results/SC1401
```

### Expected result

```text
final_state:          AMBIGUOUS_ARCHITECTURE
primary_architecture:
competing_serovars:   11,1
species_status:       SPECIES_OK
capsule_detected:     True
```

### Architecture evidence

| Evidence | Serovar 11 | Serovar 1 |
|---|---:|---:|
| Architecture recovery | 1.000 | 0.833 |
| Gene content | STRONG | STRONG |
| Sequence evidence | STRONG | STRONG |
| Gene order | STRONG | STRONG |
| Adjacency | STRONG | STRONG |
| Diagnostic evidence | STRONG | STRONG |
| Completeness | STRONG | STRONG |
| Components detected | 20/20 | 15/18 |

The serovar 11-associated architecture shows complete recovery, but substantial competing serovar 1-associated evidence is also present.

Under the current Gparatype v0.2.1 hybrid interpretation rules, the result is therefore:

```text
AMBIGUOUS_ARCHITECTURE
```

rather than a forced numbered assignment.

### Interpretation

This example demonstrates that architecture recovery alone does not determine the final Gparatype result.

Gparatype considers the broader genomic evidence, including competing architectures, before producing the final interpretation. When the evidence does not support a sufficiently specific assignment under the current rules, an ambiguity state is reported.

---

## Understanding the output files

Each Gparatype analysis generates several complementary output files:

| Output file | Description |
|---|---|
| `summary.tsv` | Compact summary of the final interpretation |
| `*.gparatype_v02.txt` | Human-readable analysis report |
| `*.gparatype_v02.json` | Machine-readable complete result |
| `architecture_evidence.tsv` | Evidence for each candidate capsule architecture |
| `component_evidence.tsv` | Component-level evidence underlying the architecture analysis |

For routine interpretation, users should begin with the human-readable report or `summary.tsv`.

The architecture and component evidence files provide additional detail when investigating supported, competing, atypical, or unresolved architectures.

---

## Interpreting Gparatype results

Gparatype reports **serovar-associated genomic capsule architectures**, not validated phenotypic serovar assignments.

For example:

- `SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE` indicates that genomic evidence supports a recognized serovar-associated capsule architecture under the current Gparatype rules.

- `SEROVAR_5_OR_12` indicates support for the shared 5/12-associated genomic state without sufficient basis for separating serovar 5 from serovar 12.

- `AMBIGUOUS_ARCHITECTURE` indicates that the available genomic evidence does not support a sufficiently specific architecture assignment under the current rules.

These states are intentionally designed to distinguish supported interpretations from biologically unresolved or conflicting genomic evidence.

---

## Reproducibility

These examples were generated using:

```text
Software version: 0.2.1
Engine:           0.2.1
Database:         GparatypeDB-2026.1-freeze
```

For reproducible analyses, record the software version, engine version, database version, and input genome accession.

Results obtained using different software or database versions may differ.

---

## Research-use limitation

Gparatype v0.2.1 is intended for research into capsule-associated genomic diversity in *Glaesserella parasuis*.

The software has undergone internal development evaluation but has not yet undergone independent external or clinical validation.

These worked examples demonstrate software behavior and should not be interpreted as estimates of diagnostic or clinical performance.
