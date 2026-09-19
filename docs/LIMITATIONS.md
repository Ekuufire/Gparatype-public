# Scientific limitations (Gparatype 0.2.1)

Honest constraints for the research freeze. Read with
[REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Gparatype 0.2.1

Gparatype is a research prototype for architecture-aware genomic interpretation of *Glaesserella parasuis* capsule-associated loci. The following limitations should be considered when interpreting results.

## 1. Research and Validation Status

Gparatype 0.2.1 has **not undergone independent external or clinical validation**. The current release is intended for research and methodological development.

Results should not be considered validated diagnostic results.

## 2. Genome Assembly Quality

Gparatype operates on genome assemblies and is dependent on the quality and completeness of the input sequence.

Fragmented assemblies, contig-edge effects, unresolved regions, or incomplete capsule-associated loci may limit interpretation. The software may therefore report `ASSEMBLY_LIMITED` or `AMBIGUOUS_ARCHITECTURE` rather than making an unsupported numbered call.

## 3. Genomic Interpretation Is Not Phenotypic Serotyping

Gparatype reports **serovar-associated genomic capsule architecture**. This is not equivalent to classical serological typing or other phenotypic serotyping methods.

Differences between genomic interpretation and historical or experimental serovar labels may occur.

## 4. Unresolved Serovar Groups

Some serovar groups cannot currently be resolved with sufficient genomic evidence.

In particular, serovars **5 and 12** are reported as:

`SEROVAR_5_OR_12`

when the available evidence supports the combined interpretation. The current release does not independently distinguish serovar 5 from serovar 12.

Additional reference genomes and biological characterization are needed to further resolve difficult serovar groups.

## 5. Conservative Classification

Gparatype is designed to avoid unsupported numbered calls when genomic evidence is incomplete or conflicting.

Consequently, an ambiguous result does not necessarily indicate a software failure. Users should not manually convert `AMBIGUOUS_ARCHITECTURE` or `ASSEMBLY_LIMITED` results into a numbered serovar without additional supporting evidence.

## 6. Not for Clinical or Regulatory Use

Gparatype 0.2.1 is provided for **research and methodological development only**.

It has not been validated for clinical diagnosis, veterinary diagnostic decision-making, regulatory testing, treatment decisions, or outbreak confirmation.

Gparatype should not be used as a standalone diagnostic method.

---

**Future validation:** Independent evaluation using additional, geographically diverse, and independently characterized isolates will be important for assessing the generalizability and performance of future releases.
