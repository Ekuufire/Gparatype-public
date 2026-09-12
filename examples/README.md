# Gparatype Worked Examples

This directory provides worked examples demonstrating how to run and interpret **Gparatype v0.2.1**.

The examples were selected to illustrate three different outcomes of the architecture-aware interpretation framework:

1. a supported serovar-associated capsule architecture;
2. a biologically unresolved serovar 5/12-associated architecture; and
3. an ambiguous architecture with competing genomic evidence.

Gparatype reports **serovar-associated genomic capsule architectures**. These interpretations are based on genomic evidence and should not automatically be considered equivalent to phenotypic serovar identity.

> **Research-use notice:** Gparatype v0.2.1 is a research prototype and has not undergone independent external validation. Results should not be used as a standalone veterinary diagnostic or clinical decision-making tool.

---

## Example 1: Supported serovar 7-associated capsule architecture

### Genome

- **Organism:** *Glaesserella parasuis*
- **Strain:** vHPS7
- **NCBI nucleotide accession:** `CP049089.1`
- **Published serovar designation:** Serovar 7
- **Gparatype engine:** `0.2.1`
- **Database:** `GparatypeDB-2026.1-freeze`

This example demonstrates a straightforward supported capsule-architecture interpretation.

The strain vHPS7 has been described as serovar 7 in the literature. Gparatype independently analyzes the genome sequence without requiring a reported serovar designation for prediction.

### Run Gparatype

After obtaining the corresponding genome assembly in FASTA format, run:

```bash
gparatype \
  --input CP049089.1.fasta \
  --output-dir results/vHPS7
```

### Expected result

```text
species_status:        SPECIES_OK
capsule_detected:      True
final_state:           SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE
primary_architecture:  7
competing_serovars:    9
```

### Architecture evidence

The serovar 7-associated reference architecture shows complete recovery:

| Evidence | Serovar 7 |
|---|---:|
| Architecture recovery | 1.000 |
| Gene content | STRONG |
| Sequence evidence | STRONG |
| Gene order | STRONG |
| Adjacency | STRONG |
| Orientation | MODERATE |
| Diagnostic evidence | STRONG |
| Completeness | STRONG |
| Components detected | 19/19 |

The next-ranked competing architecture is serovar 9-associated:

| Evidence | Serovar 9 |
|---|---:|
| Architecture recovery | 0.812 |
| Gene content | STRONG |
| Sequence evidence | STRONG |
| Gene order | STRONG |
| Adjacency | STRONG |
| Diagnostic evidence | NOT_ASSESSABLE |
| Completeness | STRONG |
| Components present | 12 |
| Components partial | 1 |
| Components not detected | 3 |

The recovery fraction is a descriptive measure of architecture recovery and **should not be interpreted as a probability or confidence score**.

### Interpretation

Gparatype reports:

```text
SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE
```

with:

```text
primary_architecture: 7
```

The genomic capsule architecture is therefore consistent with the Howell serovar 7-associated reference architecture under the Gparatype v0.2.1 hybrid rules.

In this example, the Gparatype genomic interpretation is **concordant with the published serovar 7 designation of vHPS7**.

This example demonstrates the intended interpretation of a supported result:

> **A supported Gparatype result indicates that the genomic capsule-locus evidence is consistent with a recognized serovar-associated reference architecture.**

It does not, by itself, constitute independent confirmation of phenotypic serovar identity.

---

## Example 2: Shared serovar 5/12-associated capsule architecture

### Genome

- **Organism:** *Glaesserella parasuis*
- **Strain:** KL0318
- **NCBI nucleotide accession:** `CP009237.1`
- **Gparatype engine:** `0.2.1`
- **Database:** `GparatypeDB-2026.1-freeze`

This example demonstrates how Gparatype handles a genome with strong evidence for the shared serovar 5/12-associated capsule architecture.

### Run Gparatype

```bash
gparatype \
  --input CP009237.1.fasta \
  --output-dir results/KL0318
```

### Expected result

```text
species_status:        SPECIES_OK
capsule_detected:      True
final_state:           SEROVAR_5_OR_12
primary_architecture:  5_OR_12
competing_serovars:    5,12
```

### Architecture evidence

Gparatype identifies complete and strong genomic evidence for both serovar 5- and serovar 12-associated reference architectures.

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

### Interpretation

Despite complete recovery and strong genomic evidence, Gparatype does not force an individual serovar 5 or serovar 12 assignment.

Instead, it reports:

```text
SEROVAR_5_OR_12
```

This reflects the shared genomic capsule architecture represented by the current serovar 5 and serovar 12 reference framework.

The example illustrates an important design principle:

> **When the available genomic evidence does not support a more specific interpretation, Gparatype reports the unresolved state rather than forcing an unsupported numbered assignment.**

The result represents a genomic capsule-architecture interpretation and should not be considered confirmation of phenotypic serovar identity.

---

## Example 3: Ambiguous architecture with competing genomic evidence

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
species_status:        SPECIES_OK
capsule_detected:      True
final_state:           AMBIGUOUS_ARCHITECTURE
competing_serovars:    11,1
```

### Architecture evidence

The strongest candidate is the serovar 11-associated architecture.

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

Although the serovar 11-associated architecture shows complete recovery, substantial competing serovar 1-associated genomic evidence is also present.

Under the current Gparatype v0.2.1 hybrid interpretation rules, this combination is reported conservatively as:

```text
AMBIGUOUS_ARCHITECTURE
```

rather than forcing a numbered assignment.

### Interpretation

This example demonstrates that the highest architecture-recovery value does not automatically determine the final Gparatype result.

Gparatype evaluates the broader evidence context, including competing architectures, before producing the final interpretation.

When competing genomic evidence prevents a sufficiently specific interpretation under the current rules, an ambiguity state is reported instead of an unsupported numbered assignment.

---

## Comparison of the worked examples

| Example | Genome | Gparatype result | Main lesson |
|---|---|---|---|
| 1 | vHPS7 (`CP049089.1`) | `SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE` — architecture 7 | Strong genomic evidence supports a recognized architecture |
| 2 | KL0318 (`CP009237.1`) | `SEROVAR_5_OR_12` | Strong evidence does not justify unsupported 5-versus-12 discrimination |
| 3 | SC1401 (`CP015099.1`) | `AMBIGUOUS_ARCHITECTURE` | Competing genomic evidence can prevent a forced numbered assignment |

Together, these examples illustrate a central principle of Gparatype:

> **The framework is designed to report the level of interpretation supported by the genomic evidence rather than always producing a numbered serovar-associated assignment.**

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

### `SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE`

The genomic evidence supports a recognized serovar-associated capsule architecture under the current Gparatype rules.

A supported architecture should not automatically be interpreted as independent confirmation of phenotypic serovar identity.

### `SEROVAR_5_OR_12`

The genomic evidence supports the shared serovar 5/12-associated state without sufficient basis for separating serovar 5 from serovar 12.

### `AMBIGUOUS_ARCHITECTURE`

The available genomic evidence supports more than one plausible interpretation or otherwise does not satisfy the current rules for a sufficiently specific supported assignment.

These result states are intentionally designed to distinguish supported genomic interpretations from biologically unresolved or conflicting evidence.

---

## Reproducibility

These examples were generated using:

```text
Software version: 0.2.1
Engine:           0.2.1
Interpretation:   hybrid
Database:         GparatypeDB-2026.1-freeze
Database checksum:
b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a
```

For reproducible analyses, record the software version, engine version, database version, database checksum, and input genome accession.

Results obtained using different software, engine, or database versions may differ.

---

## Obtaining the example genomes

Complete genome sequences are not redistributed with these worked examples.

Users should obtain the corresponding nucleotide sequences from the original public sequence repositories using the accessions listed above:

```text
CP049089.1    vHPS7
CP009237.1    KL0318
CP015099.1    SC1401
```

The downloaded nucleotide sequence should be provided to Gparatype as a FASTA file.

---

## Important interpretation note

The `recovery_fraction` reported by Gparatype describes recovery of components belonging to a reference capsule architecture.

It is **not a probability that an isolate belongs to a serovar**, and values for competing architectures may reflect shared or conserved capsule-associated genes.

Final interpretation therefore considers multiple forms of evidence rather than selecting a serovar solely because it has the highest recovery fraction.

---

## Research-use limitation

Gparatype v0.2.1 is intended for research into capsule-associated genomic diversity in *Glaesserella parasuis*.

The software has undergone internal development evaluation but has not yet undergone independent external or clinical validation.

These worked examples demonstrate software behavior and should not be interpreted as estimates of diagnostic or clinical performance.
