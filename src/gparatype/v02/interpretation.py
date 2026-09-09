"""Interpret architecture evidence profiles into Phase 4E result states.

Failure-safety: prefer UNRESOLVED/AMBIGUOUS over forced numbered calls.
No strain-specific exceptions. No discovery-genome tuning.
"""

from __future__ import annotations

from gparatype.v02.constants import (
    DEVELOPMENT_DEFAULT_COMPETING_DELTA,
    DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT,
)
from gparatype.v02.models import ArchitectureEvidenceProfile, InterpretationResult


def _mode_for(p: ArchitectureEvidenceProfile) -> str:
    return (p.evidence_mode or "").strip().upper()


def _is_5_or_12(sero: int) -> bool:
    return sero in (5, 12)


def _architecture_supportive(p: ArchitectureEvidenceProfile) -> bool:
    return p.content_evidence in ("STRONG", "MODERATE") and p.recovery_fraction >= DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT


def _order_or_adj_ok(p: ArchitectureEvidenceProfile) -> bool:
    return p.order_evidence in ("STRONG", "MODERATE") or p.adjacency_evidence in ("STRONG", "MODERATE")


def _diag_strong(p: ArchitectureEvidenceProfile) -> bool:
    return p.diagnostic_evidence in ("STRONG", "MODERATE")


def _metadata_agreement(reported: str | None, primary: str) -> str:
    if not reported or not str(reported).strip():
        return "NOT_SUPPLIED"
    rep = str(reported).strip().upper().replace("SEROVAR", "").replace(" ", "")
    prim = primary.strip().upper()
    if prim in ("5_OR_12", "5OR12") and rep in ("5", "12", "5_OR_12", "5OR12", "5/12"):
        return "AGREE"
    if rep == prim or rep == prim.replace("_OR_", "/"):
        return "AGREE"
    return "DISCORDANT_METADATA"


def interpret_profiles(
    profiles: list[ArchitectureEvidenceProfile],
    *,
    species_status: str,
    capsule_detected: bool,
    reported_serovar: str | None = None,
    competing_delta: float = DEVELOPMENT_DEFAULT_COMPETING_DELTA,
) -> InterpretationResult:
    warnings: list[str] = []
    for p in profiles:
        warnings.extend(p.warnings)

    if species_status == "SPECIES_CHECK_FAILED":
        return InterpretationResult(
            final_state="SPECIES_CHECK_FAILED",
            primary_architecture_serovar="",
            interpretation="Species check failed (Howell CDS homology proxy); "
            "no normal serovar architecture call emitted.",
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, ""),
            species_status=species_status,
        )

    if species_status == "SPECIES_WEAK":
        warnings.append("Proceeding with SPECIES_WEAK warning; interpretation may be unreliable.")

    ranked = sorted(profiles, key=lambda p: p.recovery_fraction, reverse=True)
    if not ranked or ranked[0].recovery_fraction <= 0 or not capsule_detected:
        return InterpretationResult(
            final_state="NO_RECOGNIZED_CAPSULE_ARCHITECTURE",
            primary_architecture_serovar="",
            interpretation="No recognizable Howell capsule architecture recovered.",
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, ""),
            species_status=species_status,
        )

    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None

    # Too few components overall across best architecture
    if best.recovery_fraction < 0.25 and best.content_evidence in ("WEAK", "INDETERMINATE", "NOT_ASSESSABLE"):
        # Check global recoverable components
        total_rec = sum(
            (p.architecture.n_present + p.architecture.n_partial) if p.architecture else 0
            for p in profiles
        )
        if total_rec < 3:
            return InterpretationResult(
                final_state="INSUFFICIENT_CAPSULE_SEQUENCE",
                primary_architecture_serovar="",
                interpretation="Capsule-associated evidence too incomplete for architecture interpretation.",
                warnings=warnings,
                metadata_agreement=_metadata_agreement(reported_serovar, ""),
                species_status=species_status,
            )

    # Assembly limitations dominate missingness on best
    if best.architecture and best.architecture.assembly_limited:
        n_exp = best.architecture.n_expected or 1
        if best.architecture.n_not_observable / n_exp >= 0.3 and best.recovery_fraction < 0.75:
            return InterpretationResult(
                final_state="ASSEMBLY_LIMITED",
                primary_architecture_serovar=str(best.serovar),
                interpretation="Assembly quality limits capsule-architecture interpretation "
                "(contig-edge / split-locus effects).",
                competing_serovars=[str(second.serovar)] if second else [],
                warnings=warnings,
                metadata_agreement=_metadata_agreement(reported_serovar, str(best.serovar)),
                species_status=species_status,
            )

    # SPECIAL_CASE_5_12
    if _is_5_or_12(best.serovar) or (
        second and _is_5_or_12(best.serovar) and _is_5_or_12(second.serovar)
    ):
        # If best is 5 or 12 (or both top), return SEROVAR_5_OR_12
        top_pair = _is_5_or_12(best.serovar) and (
            second is None
            or _is_5_or_12(second.serovar)
            or (best.recovery_fraction - second.recovery_fraction) > competing_delta
            or second.recovery_fraction < DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT
        )
        # Also if both 5 and 12 are the top two
        both_top = (
            second is not None
            and {_is_5_or_12(best.serovar), _is_5_or_12(second.serovar)} == {True}
            and _is_5_or_12(best.serovar)
            and _is_5_or_12(second.serovar)
        )
        if top_pair or both_top or _is_5_or_12(best.serovar):
            # Only emit 5_OR_12 when architecture content is at least moderate for 5 or 12
            if best.recovery_fraction >= 0.35:
                # Ensure we never force exact 5 or 12
                return InterpretationResult(
                    final_state="SEROVAR_5_OR_12",
                    primary_architecture_serovar="5_OR_12",
                    interpretation="5_OR_12-like",
                    competing_serovars=["5", "12"],
                    warnings=warnings
                    + ["SPECIAL_CASE_5_12: never emit forced serovar 5 or 12 alone."],
                    metadata_agreement=_metadata_agreement(reported_serovar, "5_OR_12"),
                    species_status=species_status,
                )

    # Competing (non 5/12 pair)
    if (
        second is not None
        and (best.recovery_fraction - second.recovery_fraction) <= competing_delta
        and not (_is_5_or_12(best.serovar) and _is_5_or_12(second.serovar))
        and second.recovery_fraction >= 0.25
    ):
        return InterpretationResult(
            final_state="AMBIGUOUS_ARCHITECTURE",
            primary_architecture_serovar="",
            interpretation=(
                f"Competing architectures within DEVELOPMENT delta "
                f"(best={best.serovar}@{best.recovery_fraction:.2f}, "
                f"second={second.serovar}@{second.recovery_fraction:.2f})."
            ),
            competing_serovars=[str(best.serovar), str(second.serovar)],
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, ""),
            species_status=species_status,
        )

    # Conflicting: diagnostic strongly supports one, architecture another
    diag_best = max(profiles, key=lambda p: _diag_rank(p.diagnostic_evidence))
    if (
        _diag_strong(diag_best)
        and diag_best.serovar != best.serovar
        and _architecture_supportive(best)
        and not (_is_5_or_12(diag_best.serovar) and _is_5_or_12(best.serovar))
    ):
        # Serovar 11 amtA-alone guard also covered below
        return InterpretationResult(
            final_state="CONFLICTING_GENOMIC_EVIDENCE",
            primary_architecture_serovar="",
            interpretation=(
                f"Diagnostic region favors serovar {diag_best.serovar} while architecture "
                f"content favors serovar {best.serovar}."
            ),
            competing_serovars=[str(best.serovar), str(diag_best.serovar)],
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, ""),
            species_status=species_status,
        )

    # Serovar 11: NEVER emit SUPPORTED unless architecture content strong AND mode allows;
    # amtA-alone must NOT yield SUPPORTED.
    if best.serovar == 11:
        mode = _mode_for(best)
        amtA_only = (
            best.diagnostic_evidence in ("STRONG", "MODERATE")
            and best.content_evidence in ("WEAK", "INDETERMINATE", "NOT_ASSESSABLE")
        )
        if amtA_only or best.content_evidence != "STRONG" or mode == "INSUFFICIENT_REFERENCE_DATA":
            state = "AMBIGUOUS_ARCHITECTURE"
            if best.recovery_fraction < 0.35:
                state = "INSUFFICIENT_CAPSULE_SEQUENCE"
            elif _diag_strong(best) and not _architecture_supportive(best):
                state = "CONFLICTING_GENOMIC_EVIDENCE"
            return InterpretationResult(
                final_state=state,
                primary_architecture_serovar="",
                interpretation=(
                    "Serovar 11: unqualified call from amtA alone is not permitted; "
                    "architecture content insufficient for SUPPORTED."
                ),
                competing_serovars=[str(best.serovar)],
                warnings=warnings
                + ["Serovar 11 mode INSUFFICIENT_REFERENCE_DATA / amtA-alone guard."],
                metadata_agreement=_metadata_agreement(reported_serovar, ""),
                species_status=species_status,
            )

    # Mode-specific support gates for single best
    mode = _mode_for(best)
    supported_ok = False
    if mode == "SPECIAL_CASE_5_12":
        # handled above
        supported_ok = False
    elif mode == "SINGLE_TARGET_WITH_ARCHITECTURE_CONFIRMATION":
        # Serovar 8/9: need diagnostic support AND architecture confirmation
        supported_ok = _diag_strong(best) and _architecture_supportive(best) and (
            _order_or_adj_ok(best) or best.content_evidence == "STRONG"
        )
    elif mode == "ARCHITECTURE_SUPPORTED":
        # Serovar 7/13: architecture primary; mark provisional in warnings
        warnings.append(f"Serovar {best.serovar}: ARCHITECTURE_SUPPORTED mode; validation_readiness provisional.")
        supported_ok = _architecture_supportive(best) and (
            _order_or_adj_ok(best) or best.content_evidence == "STRONG"
        )
    elif mode == "HYBRID_TARGET_ARCHITECTURE":
        supported_ok = _architecture_supportive(best) and (
            _diag_strong(best) or _order_or_adj_ok(best)
        )
    elif mode == "INSUFFICIENT_REFERENCE_DATA":
        supported_ok = False
    else:
        # Unknown / empty mode: require strong architecture + order/adj
        supported_ok = best.content_evidence == "STRONG" and _order_or_adj_ok(best)

    # Atypical: sufficient sequence but substantial deviation from all refs
    if (
        best.recovery_fraction >= 0.35
        and best.content_evidence in ("WEAK", "INDETERMINATE")
        and all(p.recovery_fraction < DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT for p in profiles)
    ):
        return InterpretationResult(
            final_state="ATYPICAL_CAPSULE_PROFILE",
            primary_architecture_serovar="",
            interpretation="Sufficient capsule sequence observed but no canonical Howell architecture fits cleanly.",
            competing_serovars=[str(p.serovar) for p in ranked[:3]],
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, ""),
            species_status=species_status,
        )

    if supported_ok and not (_is_5_or_12(best.serovar)):
        # Prefer AMBIGUOUS over unsupported readiness forcing — still allow SUPPORTED with readiness warning
        if best.readiness == "INSUFFICIENT_DATA":
            return InterpretationResult(
                final_state="AMBIGUOUS_ARCHITECTURE",
                primary_architecture_serovar="",
                interpretation=f"Readiness INSUFFICIENT_DATA for serovar {best.serovar}; refusing SUPPORTED call.",
                competing_serovars=[str(best.serovar)],
                warnings=warnings,
                metadata_agreement=_metadata_agreement(reported_serovar, ""),
                species_status=species_status,
            )
        return InterpretationResult(
            final_state="SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE",
            primary_architecture_serovar=str(best.serovar),
            interpretation=(
                f"Genomic capsule architecture is consistent with Howell serovar "
                f"{best.serovar}-associated reference architecture "
                f"(recovery_fraction={best.recovery_fraction:.2f}; not a phenotypic call)."
            ),
            competing_serovars=[str(second.serovar)] if second else [],
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, str(best.serovar)),
            species_status=species_status,
            details={"evidence_mode": mode, "recovery_fraction": best.recovery_fraction},
        )

    # Failure-safety default
    if best.recovery_fraction >= DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT:
        return InterpretationResult(
            final_state="AMBIGUOUS_ARCHITECTURE",
            primary_architecture_serovar="",
            interpretation=(
                f"Best architecture serovar {best.serovar} lacks mode-appropriate support "
                f"for a SUPPORTED call; preferring AMBIGUOUS."
            ),
            competing_serovars=[str(best.serovar)] + ([str(second.serovar)] if second else []),
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, ""),
            species_status=species_status,
        )

    if best.recovery_fraction > 0:
        return InterpretationResult(
            final_state="INSUFFICIENT_CAPSULE_SEQUENCE",
            primary_architecture_serovar="",
            interpretation="Insufficient capsule-locus recovery for a supported architecture association.",
            warnings=warnings,
            metadata_agreement=_metadata_agreement(reported_serovar, ""),
            species_status=species_status,
        )

    return InterpretationResult(
        final_state="NO_RECOGNIZED_CAPSULE_ARCHITECTURE",
        primary_architecture_serovar="",
        interpretation="No recognized Howell capsule architecture detected.",
        warnings=warnings,
        metadata_agreement=_metadata_agreement(reported_serovar, ""),
        species_status=species_status,
    )


def _diag_rank(label: str) -> int:
    return {"STRONG": 4, "MODERATE": 3, "WEAK": 2, "INDETERMINATE": 1}.get(label, 0)
