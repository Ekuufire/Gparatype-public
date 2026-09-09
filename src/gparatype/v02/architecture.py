"""Canonical architecture profiling vs Howell reference architectures."""

from __future__ import annotations

from gparatype.utils import parse_fasta
from gparatype.v02.capsule_locator import label_hit_presence
from gparatype.v02.constants import DEVELOPMENT_DEFAULT_EDGE_BP
from gparatype.v02.database import GparatypeDatabase
from gparatype.v02.models import ArchitectureProfile, ComponentHit, ComponentStatus
from pathlib import Path


def _contig_lengths(genome_fasta: Path) -> dict[str, int]:
    lengths: dict[str, int] = {}
    for hdr, seq in parse_fasta(genome_fasta):
        lengths[hdr.split()[0]] = len(seq)
    return lengths


def _near_edge(start: int, end: int, contig_len: int, edge_bp: int) -> bool:
    return start <= edge_bp or (contig_len - end) <= edge_bp


def build_architecture_profiles(
    db: GparatypeDatabase,
    search_hits: list[ComponentHit],
    genome_fasta: Path,
    *,
    edge_bp: int = DEVELOPMENT_DEFAULT_EDGE_BP,
) -> list[ArchitectureProfile]:
    """Build one ArchitectureProfile per canonical serovar (1–15)."""
    by_acc = {h.accession: h for h in search_hits}
    contig_len = _contig_lengths(genome_fasta)
    profiles: list[ArchitectureProfile] = []

    for serovar in range(1, 16):
        expected = db.architecture_for(serovar)
        strain = db.serovars[serovar].strain if serovar in db.serovars else ""
        components: list[ComponentStatus] = []
        found_hits: list[tuple[ComponentStatus, ComponentHit]] = []

        for comp in expected:
            hit = by_acc.get(comp.accession)
            if hit is None:
                components.append(
                    ComponentStatus(
                        component_id=comp.component_id,
                        serovar=serovar,
                        gene=comp.gene_name,
                        accession=comp.accession,
                        gene_order=comp.gene_order,
                        status="NOT_DETECTED",
                    )
                )
                continue
            lab = label_hit_presence(hit)
            status = "PRESENT" if lab == "PRESENT" else ("PARTIAL" if lab == "PARTIAL" else "PARTIAL")
            clen = contig_len.get(hit.contig, 0)
            near = _near_edge(hit.subject_start, hit.subject_end, clen, edge_bp) if clen else False
            cs = ComponentStatus(
                component_id=comp.component_id,
                serovar=serovar,
                gene=comp.gene_name,
                accession=comp.accession,
                gene_order=comp.gene_order,
                status=status,
                percent_identity=hit.percent_identity,
                query_coverage=hit.query_coverage,
                contig=hit.contig,
                subject_start=hit.subject_start,
                subject_end=hit.subject_end,
                strand=hit.strand,
                near_contig_edge=near,
            )
            components.append(cs)
            found_hits.append((cs, hit))

        # Contig-edge NOT_OBSERVABLE rule (conservative):
        # If ANY expected components are found and the recovered locus sits at contig
        # termini, mark missing components as NOT_OBSERVABLE rather than NOT_DETECTED
        # when plausible (hits within EDGE_BP of contig end).
        any_found = any(c.status in ("PRESENT", "PARTIAL") for c in components)
        locus_at_edge = any(c.near_contig_edge for c, _ in found_hits)
        # Also: if found components span multiple contigs (split locus), mark missing as NOT_OBSERVABLE
        contigs_used = {c.contig for c, _ in found_hits if c.contig}
        split_locus = len(contigs_used) > 1
        assembly_limited = False
        if any_found and (locus_at_edge or split_locus):
            assembly_limited = True
            for c in components:
                if c.status == "NOT_DETECTED":
                    c.status = "NOT_OBSERVABLE"

        n_present = sum(1 for c in components if c.status == "PRESENT")
        n_partial = sum(1 for c in components if c.status == "PARTIAL")
        n_nd = sum(1 for c in components if c.status == "NOT_DETECTED")
        n_no = sum(1 for c in components if c.status == "NOT_OBSERVABLE")
        n_exp = len(components)
        recoverable = n_present + n_partial
        # Completeness: fraction of expected genes PRESENT or PARTIAL
        recovery = (recoverable / n_exp) if n_exp else 0.0

        order_status, adj_status, ori_status = _assess_synteny(components, expected)

        warnings: list[str] = []
        if assembly_limited:
            warnings.append(
                "Assembly limitation: recovered components near contig termini and/or "
                "split across contigs; absences labeled NOT_OBSERVABLE where applicable."
            )

        profiles.append(
            ArchitectureProfile(
                serovar=serovar,
                reference_strain=strain,
                n_expected=n_exp,
                n_present=n_present,
                n_partial=n_partial,
                n_not_detected=n_nd,
                n_not_observable=n_no,
                recovery_fraction=recovery,
                order_status=order_status,
                adjacency_status=adj_status,
                orientation_status=ori_status,
                assembly_limited=assembly_limited,
                components=components,
                warnings=warnings,
            )
        )
    return profiles


def _assess_synteny(components: list[ComponentStatus], expected) -> tuple[str, str, str]:
    """Order / adjacency / orientation for same-contig observed components."""
    observed = [c for c in components if c.status in ("PRESENT", "PARTIAL") and c.contig]
    if len(observed) < 2:
        return "ORDER_NOT_ASSESSABLE", "ADJACENCY_NOT_ASSESSABLE", "ORIENTATION_NOT_ASSESSABLE"

    # Group by contig
    by_contig: dict[str, list[ComponentStatus]] = {}
    for c in observed:
        by_contig.setdefault(c.contig, []).append(c)

    order_labels: list[str] = []
    adj_labels: list[str] = []
    ori_labels: list[str] = []

    for contig, rows in by_contig.items():
        if len(rows) < 2:
            order_labels.append("ORDER_NOT_ASSESSABLE")
            adj_labels.append("ADJACENCY_NOT_ASSESSABLE")
            continue
        # Sort by genomic coordinate midpoint
        rows_sorted = sorted(
            rows, key=lambda c: ((c.subject_start or 0) + (c.subject_end or 0)) / 2
        )
        # Observed gene_order sequence
        obs_orders = [c.gene_order for c in rows_sorted]
        # Agree if monotonic increasing or decreasing (reverse strand locus)
        increasing = all(obs_orders[i] < obs_orders[i + 1] for i in range(len(obs_orders) - 1))
        decreasing = all(obs_orders[i] > obs_orders[i + 1] for i in range(len(obs_orders) - 1))
        if increasing or decreasing:
            order_labels.append("ORDER_AGREE")
        else:
            order_labels.append("ORDER_DISAGREE")

        # Adjacency: for consecutive expected neighbors present on same contig,
        # check they are consecutive in observed sorted order among recovered set
        gene_to_comp = {c.gene: c for c in components}
        agree = 0
        total = 0
        for i in range(len(expected) - 1):
            a = expected[i]
            b = expected[i + 1]
            ca = next((c for c in components if c.accession == a.accession), None)
            cb = next((c for c in components if c.accession == b.accession), None)
            if ca is None or cb is None:
                continue
            if ca.status not in ("PRESENT", "PARTIAL") or cb.status not in ("PRESENT", "PARTIAL"):
                continue
            if ca.contig != contig or cb.contig != contig or ca.contig != cb.contig:
                continue
            total += 1
            # Midpoints
            ma = ((ca.subject_start or 0) + (ca.subject_end or 0)) / 2
            mb = ((cb.subject_start or 0) + (cb.subject_end or 0)) / 2
            # Check no other observed component of this serovar lies strictly between them
            between = [
                c
                for c in rows_sorted
                if c.accession not in (ca.accession, cb.accession)
                and min(ma, mb) < ((c.subject_start or 0) + (c.subject_end or 0)) / 2 < max(ma, mb)
            ]
            # Ideal: consecutive in gene_order and no intervening expected gene that was found
            if not between:
                agree += 1
        if total == 0:
            adj_labels.append("ADJACENCY_NOT_ASSESSABLE")
        elif agree / total >= 0.7:
            adj_labels.append("ADJACENCY_AGREE")
        else:
            adj_labels.append("ADJACENCY_DISAGREE")

        # Orientation: reference assumed PLUS; if decreasing order, expect minus strands majority
        plus = sum(1 for c in rows_sorted if c.strand == "plus")
        minus = sum(1 for c in rows_sorted if c.strand == "minus")
        if plus + minus == 0:
            ori_labels.append("ORIENTATION_NOT_ASSESSABLE")
        elif increasing and plus >= minus:
            ori_labels.append("ORIENTATION_AGREE")
        elif decreasing and minus >= plus:
            ori_labels.append("ORIENTATION_AGREE")
        elif plus == 0 or minus == 0:
            # Uniform strand with order: treat as assessable supportive
            ori_labels.append("ORIENTATION_AGREE" if (increasing or decreasing) else "ORIENTATION_DISAGREE")
        else:
            ori_labels.append("ORIENTATION_DISAGREE")

    def _collapse(labels: list[str], agree: str, disagree: str, na: str) -> str:
        if not labels:
            return na
        if any(l == disagree for l in labels):
            return disagree
        if any(l == agree for l in labels):
            return agree
        return na

    return (
        _collapse(order_labels, "ORDER_AGREE", "ORDER_DISAGREE", "ORDER_NOT_ASSESSABLE"),
        _collapse(adj_labels, "ADJACENCY_AGREE", "ADJACENCY_DISAGREE", "ADJACENCY_NOT_ASSESSABLE"),
        _collapse(ori_labels, "ORIENTATION_AGREE", "ORIENTATION_DISAGREE", "ORIENTATION_NOT_ASSESSABLE"),
    )
