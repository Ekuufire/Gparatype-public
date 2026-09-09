# Examples (public distribution)

This directory documents **how to invoke** Gparatype. It does **not** redistribute
whole-genome assemblies with unclear redistribution rights.

## Input requirements

- **Whole-genome assembly FASTA** (`.fasta`, `.fa`, `.fna`) — **not FASTQ**
- Single isolate / sample per run
- Reasonably contiguous assembly preferred; fragmented loci may yield `ASSEMBLY_LIMITED`

## Recommended command (engine 0.2.1)

Default database is the bundled freeze DB; `--database` is optional:

```bash
gparatype --input <assembly.fasta> \
  --engine 0.2.1 \
  --output-dir results/example_run
```

Flags:

- `--input` / `-i` — **required**
- `--engine` — default `0.2.1`; legacy `0.2` / `0.1.1` for reproducibility only
- `--database` — override path (default: `data/gparatype_db/GparatypeDB-2026.1-freeze`)
- `--output-dir` / `-o` — output directory
- `--reported-serovar` — metadata for reporting only; **must not** influence prediction

Also: `python -m gparatype` with the same arguments.

## Obtaining a public assembly (accession-based)

No redistributable validation genome is bundled. To run on a public record:

1. Download a *G. parasuis* assembly from NCBI Assembly or Datasets CLI using a
   public accession (e.g. search NCBI for *Glaesserella parasuis* complete or
   draft genomes with explicit redistribution terms).
2. Run Gparatype on the downloaded FASTA.

**Do not fabricate an expected serovar** unless you have independent metadata
(serology, publication label, or curated validation record). Report the engine
`final_state` and interpretation text without claiming external validation.

Example shape (replace paths and accession):

```bash
# Illustrative — download step depends on your NCBI tooling
datasets download genome accession GCF_XXXXXX.X --filename isolate.fna.gz
gzip -dc isolate.fna.gz > isolate.fasta

gparatype --input isolate.fasta \
  --engine 0.2.1 \
  --output-dir results/ncbi_example
```

Inspect `<sample>.gparatype_v02.txt` and `summary.tsv` for result state and warnings.

## SOFTWARE_UNIT_TEST_ONLY — BLAST plumbing

To confirm CLI / BLAST wiring without a typing cohort genome, you may use a
**single CDS record** extracted from the bundled database FASTA as a toy subject.
This is **not** biological validation and **not** interpretable serovar typing:

```bash
# Extract one header/sequence from bundled reference (example gene accession KC795327.1)
grep -A1 'KC795327.1' data/gparatype_db/GparatypeDB-2026.1-freeze/howell_cds_all.fasta \
  | head -2 > /tmp/toy_cds.fasta

gparatype --input /tmp/toy_cds.fasta \
  --engine 0.2.1 \
  --output-dir results/software_only
```

Label such runs: **SOFTWARE_UNIT_TEST_ONLY**.

## Output files (engine 0.2.1)

| File | Description |
|---|---|
| `<sample>.gparatype_v02.txt` | Text report: `final_state`, architecture, interpretation |
| `<sample>.gparatype_v02.json` | JSON payload |
| `summary.tsv` | One-row summary |
| `architecture_evidence.tsv` | Architecture evidence table |
| `component_evidence.tsv` | Component evidence table |

Console line shape (values depend on input):

```text
<final_state>	primary=<serovar_or_->	<interpretation text>
```

Possible `final_state` values: see `V02_RESULT_STATES` in `src/gparatype/__init__.py`.
