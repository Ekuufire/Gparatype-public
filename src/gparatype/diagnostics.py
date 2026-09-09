"""Phase 3C diagnostic-region helpers (amplicon/primer reconstruction).

Does not modify serovar calling logic.
"""

from __future__ import annotations

from dataclasses import dataclass


def revcomp(seq: str) -> str:
    comp = str.maketrans("ACGTRYSWKMBDHVNacgtryswkmbdhvn", "TGCAYRSWMKVHDBNtgcayrswmkvhdbn")
    return seq.translate(comp)[::-1]


@dataclass(frozen=True)
class PrimerHit:
    start: int  # 0-based inclusive
    end: int  # 0-based exclusive
    strand: str  # plus | minus
    identity: float
    mismatches: int


def find_exact(haystack: str, needle: str) -> list[tuple[int, int]]:
    """Return all exact occurrences as (start, end) 0-based half-open."""
    if not needle:
        return []
    out: list[tuple[int, int]] = []
    start = 0
    h = haystack.upper()
    n = needle.upper()
    while True:
        i = h.find(n, start)
        if i < 0:
            break
        out.append((i, i + len(n)))
        start = i + 1
    return out


def find_best_near_exact(haystack: str, needle: str, max_mismatch: int = 0) -> PrimerHit | None:
    """Find best window match allowing up to max_mismatch substitutions (no indels)."""
    h = haystack.upper()
    n = needle.upper()
    if not n or len(n) > len(h):
        return None
    best: PrimerHit | None = None
    for i in range(0, len(h) - len(n) + 1):
        window = h[i : i + len(n)]
        mm = sum(a != b for a, b in zip(window, n))
        if mm <= max_mismatch:
            ident = 100.0 * (len(n) - mm) / len(n)
            hit = PrimerHit(i, i + len(n), "plus", ident, mm)
            if best is None or hit.mismatches < best.mismatches or (
                hit.mismatches == best.mismatches and hit.identity > best.identity
            ):
                best = hit
    return best


def find_primer_on_sequence(seq: str, primer: str, max_mismatch: int = 0) -> list[PrimerHit]:
    """Find primer on plus strand and its RC on the sequence (stored as minus)."""
    hits: list[PrimerHit] = []
    if max_mismatch == 0:
        for s, e in find_exact(seq, primer):
            hits.append(PrimerHit(s, e, "plus", 100.0, 0))
        rc = revcomp(primer)
        for s, e in find_exact(seq, rc):
            hits.append(PrimerHit(s, e, "minus", 100.0, 0))
        return hits
    plus = find_best_near_exact(seq, primer, max_mismatch=max_mismatch)
    if plus:
        hits.append(plus)
    minus = find_best_near_exact(seq, revcomp(primer), max_mismatch=max_mismatch)
    if minus:
        hits.append(PrimerHit(minus.start, minus.end, "minus", minus.identity, minus.mismatches))
    return hits


@dataclass
class AmpliconReconstruction:
    serovar_call: str
    target_gene: str
    target_accession: str
    forward_primer: str
    reverse_primer: str
    forward_start: int | None  # 1-based inclusive on CDS
    forward_end: int | None
    reverse_start: int | None
    reverse_end: int | None
    expected_amplicon_bp_published: int
    reconstructed_amplicon_bp: int | None
    amplicon_seq: str
    reconstruction_status: str
    notes: str


def reconstruct_amplicon_from_cds(
    cds_seq: str,
    *,
    serovar_call: str,
    target_gene: str,
    target_accession: str,
    forward_primer: str,
    reverse_primer: str,
    expected_amplicon_bp: int,
    exact_only: bool = True,
) -> AmpliconReconstruction:
    """Map published primers onto a validated target CDS and extract amplicon.

    Standard PCR geometry on coding strand:
    - forward primer on plus strand
    - reverse primer as RC (stored as minus-strand site on the CDS)
    - product from forward start through reverse site end
    """
    max_mm = 0 if exact_only else 1
    fwd_hits = [h for h in find_primer_on_sequence(cds_seq, forward_primer, max_mismatch=max_mm) if h.strand == "plus"]
    rev_hits = [h for h in find_primer_on_sequence(cds_seq, reverse_primer, max_mismatch=max_mm) if h.strand == "minus"]

    if not fwd_hits and not rev_hits:
        return AmpliconReconstruction(
            serovar_call,
            target_gene,
            target_accession,
            forward_primer,
            reverse_primer,
            None,
            None,
            None,
            None,
            expected_amplicon_bp,
            None,
            "",
            "FAIL_NO_PRIMER_SITES",
            "Neither forward nor reverse primer mapped exactly to CDS",
        )
    if not fwd_hits:
        rh = rev_hits[0]
        return AmpliconReconstruction(
            serovar_call,
            target_gene,
            target_accession,
            forward_primer,
            reverse_primer,
            None,
            None,
            rh.start + 1,
            rh.end,
            expected_amplicon_bp,
            None,
            "",
            "FAIL_FORWARD_NOT_FOUND",
            "Forward primer site not found exactly on CDS",
        )
    if not rev_hits:
        fh = fwd_hits[0]
        return AmpliconReconstruction(
            serovar_call,
            target_gene,
            target_accession,
            forward_primer,
            reverse_primer,
            fh.start + 1,
            fh.end,
            None,
            None,
            expected_amplicon_bp,
            None,
            "",
            "FAIL_REVERSE_NOT_FOUND",
            "Reverse primer site not found exactly on CDS",
        )

    # Choose geometry: forward before reverse site on the sequence
    candidates = []
    for fh in fwd_hits:
        for rh in rev_hits:
            if fh.start < rh.end and rh.start >= fh.end - len(reverse_primer):
                # product inclusive of both primers
                start = fh.start
                end = rh.end
                if end > start:
                    amp = cds_seq[start:end]
                    candidates.append((fh, rh, amp))
    if not candidates:
        fh, rh = fwd_hits[0], rev_hits[0]
        return AmpliconReconstruction(
            serovar_call,
            target_gene,
            target_accession,
            forward_primer,
            reverse_primer,
            fh.start + 1,
            fh.end,
            rh.start + 1,
            rh.end,
            expected_amplicon_bp,
            None,
            "",
            "FAIL_ORIENTATION_OR_ORDER",
            f"Primer sites found but not in forward→reverse order (fwd={fh.start}-{fh.end}, rev={rh.start}-{rh.end})",
        )

    # Prefer product closest to published expected size
    fh, rh, amp = min(candidates, key=lambda t: abs(len(t[2]) - expected_amplicon_bp))
    status = "OK"
    notes = ""
    if abs(len(amp) - expected_amplicon_bp) > max(20, int(0.15 * expected_amplicon_bp)):
        status = "OK_SIZE_DISCREPANCY"
        notes = f"Reconstructed {len(amp)} bp vs published {expected_amplicon_bp} bp"
    return AmpliconReconstruction(
        serovar_call,
        target_gene,
        target_accession,
        forward_primer,
        reverse_primer,
        fh.start + 1,
        fh.end,
        rh.start + 1,
        rh.end,
        expected_amplicon_bp,
        len(amp),
        amp.upper(),
        status,
        notes,
    )


def predict_pcr_products(
    genome_seq_by_contig: dict[str, str],
    forward_primer: str,
    reverse_primer: str,
    expected_bp: int,
    *,
    size_tol_frac: float = 0.25,
    size_tol_abs: int = 50,
    max_mismatch: int = 0,
) -> list[dict]:
    """In-silico primer-pair scan across contigs.

    Looks for plus-strand forward and minus-strand reverse (RC of reverse primer)
    on the same contig with plausible spacing.
    """
    products: list[dict] = []
    for contig, seq in genome_seq_by_contig.items():
        fwd = [h for h in find_primer_on_sequence(seq, forward_primer, max_mismatch=max_mismatch) if h.strand == "plus"]
        rev = [h for h in find_primer_on_sequence(seq, reverse_primer, max_mismatch=max_mismatch) if h.strand == "minus"]
        for fh in fwd:
            for rh in rev:
                if fh.start < rh.end:
                    prod = rh.end - fh.start
                    tol = max(size_tol_abs, int(size_tol_frac * expected_bp))
                    products.append(
                        {
                            "contig": contig,
                            "forward_start": fh.start + 1,
                            "forward_end": fh.end,
                            "reverse_start": rh.start + 1,
                            "reverse_end": rh.end,
                            "forward_identity": fh.identity,
                            "reverse_identity": rh.identity,
                            "correct_orientation": True,
                            "predicted_product_bp": prod,
                            "size_ok": abs(prod - expected_bp) <= tol,
                        }
                    )
    return products
