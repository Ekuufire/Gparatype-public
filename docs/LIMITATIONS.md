# Scientific limitations (Gparatype 0.2.1)

Honest constraints for the research freeze. Read with
[REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## 1. No independent external validation

`EXTERNAL_VALIDATION=NOT_PERFORMED`. Phase 5F is an
**INTERNAL_DEVELOPMENT_COMPARISON** only. Do not present concordance metrics
as independent external validation.

## 2. Discovery contamination of the development cohort

The development / discovery cohort used across Phase 4–5 analyses is
**discovery-contaminated** (`DEVELOPMENT_COHORT=DISCOVERY_CONTAMINATED`).
Historically described as a ~336-genome development set; the Phase 5F CORR1
paired benchmark used **n_all=322** / **n_clean=315**. Discovery and evaluation
overlap means optimistic bias is possible.

## 3. Phase 5F internal comparison metrics (CLEAN n=315)

Frozen internal benchmark (stratum `CLEAN_EXCL_CONFLICTS`):

| Engine | Compatible concordance | False numbered-call rate | Informative call rate |
|---|---|---|---|
| 0.1.1 | 62.9% (0.6286) | 14.6% (0.1463) | 74.3% (0.7429) |
| 0.2.0 | 63.5% (0.6349) | 6.8% (0.0684) | 73.3% (0.7333) |
| 0.2.1 hybrid | 60.6% (0.6063) | 4.5% (0.0455) | 68.9% (0.6889) |

CLEAN ambiguous rate under 0.2.1 ≈ 29.5% (vs ≈ 24.4% under 0.2.0).

**Conservatism explanation:** Relative to 0.2.0, the hybrid engine **reduced
unsupported / false numbered calls** (safety gain) but also **increased
ambiguous calls** and **reduced informative call rate**, with a modest drop in
compatible concordance. This trade-off is intentional: prefer
`AMBIGUOUS_ARCHITECTURE` / abstention over incorrect numbered architecture
calls. Decision recorded: **`PROMISING_BUT_NEEDS_REFINEMENT`**.

These numbers are **not** independent external validation.

## 4. Heterogeneous metadata provenance

Reported serovars span experimental serology, molecular typing, publication
labels, NCBI attributes, and computational predictions of unequal strength.
Metadata must never be treated as hidden prediction features.

## 5. Limited independent references for difficult serovars

Phase 5D.1 found little new independent Tier-B field reference support for
several hard groups (notably 2 / 6 / 8 / 10 / 11 beyond canonical anchors and
already-used discovery-linked material). Signature readiness remains limited
for several serovars (`READY_WITH_LIMITATIONS` / `MORE_BIOLOGY_REQUIRED`).

## 6. Unresolved 2 / 8 / 10 biology

Serovars **2, 8, and 10** remain biologically unresolved at population scale.
The hybrid prototype prefers `AMBIGUOUS_ARCHITECTURE` rather than forced
numbered calls (`MORE_BIOLOGY` policy).

## 7. Combined 5 / 12 interpretation

Serovars **5 and 12** share the Howell `wcwK` target context and are emitted
only as the combined state **`SEROVAR_5_OR_12`**. They are not separated.
Phase 5F confirmed no lone split of 5 vs 12 under engine 0.2.1.

## 8. Assembly fragmentation / quality dependence

Contig-edge and split-locus effects can hide genes or truncate Region-2
modules. The engine prefers **`ASSEMBLY_LIMITED`** over claiming biological
absence when assembly quality limits interpretation.

## 9. Genomic capsule interpretation ≠ phenotypic serotyping

Gparatype reports **serovar-associated genomic capsule architecture**. This is
not equivalent to classical serological typing, mPCR clinical calls, or
automatic override of historical labels. Not intended as a standalone
veterinary diagnostic for now.

## 10. Conservative ambiguous / assembly-limited states

Increased ambiguity under the hybrid prototype is a documented safety behavior,
not a hidden failure mode to be optimized away on the discovery cohort.

## 11. Research-only status

`CLINICAL_VALIDATION=NO`. Software version **`0.2.1`** with research label
**0.2.1-research**. Not for diagnosis, clinical decision-making, or regulatory
use. Phase decision: **`PROMISING_BUT_NEEDS_REFINEMENT`**.
