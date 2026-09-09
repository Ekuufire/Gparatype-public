"""BLAST homology of Howell CDS components against a query genome."""

from __future__ import annotations

from pathlib import Path

from gparatype.blast import run_blastn
from gparatype.v02.constants import SEARCH_EVALUE, SEARCH_MIN_PIDENT, SEARCH_MIN_QCOV
from gparatype.v02.database import GparatypeDatabase
from gparatype.v02.models import ComponentHit


def _parse_query_header(qid: str) -> tuple[str, int, str, str]:
    """Parse DB FASTA header: component_id|serovar=N|gene=G|accession=A|..."""
    parts = qid.split("|")
    component_id = parts[0]
    serovar = 0
    gene = ""
    accession = ""
    for p in parts[1:]:
        if p.startswith("serovar="):
            serovar = int(p.split("=", 1)[1])
        elif p.startswith("gene="):
            gene = p.split("=", 1)[1]
        elif p.startswith("accession="):
            accession = p.split("=", 1)[1]
    return component_id, serovar, gene, accession


def run_homology(
    genome_fasta: Path,
    db: GparatypeDatabase,
    *,
    out_path: Path | None = None,
    evalue: float = SEARCH_EVALUE,
    min_pident: float = SEARCH_MIN_PIDENT,
    min_qcov: float = SEARCH_MIN_QCOV,
    retain_weaker: bool = True,
) -> tuple[list[ComponentHit], list[ComponentHit], Path]:
    """BLAST all Howell CDS (query=DB fasta) vs genome (subject).

    Returns (search_hits, all_raw_hits, blast_tsv_path).
    SEARCH hits meet SEARCH_* thresholds; raw may include weaker hits when retain_weaker.
    """
    if db.fasta_path is None or not db.fasta_path.is_file():
        raise FileNotFoundError("Database FASTA missing")

    hits, blast_path = run_blastn(db.fasta_path, genome_fasta, out_path=out_path, evalue=evalue)

    # Aggregate by (component accession, subject contig) keeping best bitscore
    best: dict[tuple[str, str], ComponentHit] = {}
    raw: list[ComponentHit] = []
    counts: dict[str, int] = {}

    for h in hits:
        component_id, serovar, gene, accession = _parse_query_header(h.query_id)
        if not accession and component_id in db.components_by_accession:
            accession = component_id
        counts[accession] = counts.get(accession, 0) + 1
        contig = h.subject_id.split()[0]
        start = min(h.subject_start, h.subject_end)
        end = max(h.subject_start, h.subject_end)
        rec = ComponentHit(
            component_id=component_id or accession,
            serovar=serovar,
            gene=gene,
            accession=accession,
            contig=contig,
            subject_start=start,
            subject_end=end,
            strand=h.strand,
            percent_identity=h.percent_identity,
            query_coverage=h.query_coverage,
            alignment_length=h.alignment_length,
            mismatches=h.mismatches,
            gaps=h.gaps,
            bitscore=h.bitscore,
            evalue=h.evalue,
            hit_count=1,
            query_length=h.query_length,
        )
        raw.append(rec)
        key = (accession, contig)
        prev = best.get(key)
        if prev is None or rec.bitscore > prev.bitscore:
            best[key] = rec

    # Also keep best overall per accession (across contigs)
    best_acc: dict[str, ComponentHit] = {}
    for rec in best.values():
        prev = best_acc.get(rec.accession)
        if prev is None or rec.bitscore > prev.bitscore:
            best_acc[rec.accession] = rec

    for acc, rec in best_acc.items():
        rec.hit_count = counts.get(acc, 1)

    search_hits = [
        rec
        for rec in best_acc.values()
        if rec.percent_identity >= min_pident and rec.query_coverage >= min_qcov
    ]
    if retain_weaker:
        return search_hits, list(best_acc.values()), blast_path
    return search_hits, search_hits, blast_path
