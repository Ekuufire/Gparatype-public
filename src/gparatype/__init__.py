"""Gparatype — research prototype for G. parasuis capsule/serovar genomic interpretation."""

__version__ = "0.2.1"

# Baseline engine retained for --engine 0.1.1 (Phase 3C.1 / engine commit f784c655).
BASELINE_ENGINE_VERSION = "0.1.1-dev"
# Engine implementation commit (Phase 3C.1 diagnostic evidence hierarchy):
# f784c6554c1d7de0944d28fc82ee8596df9d5ff7

# Phase 5E hybrid research prototype (default CLI engine 0.2.1).
HYBRID_ENGINE_VERSION = "0.2.1-dev"
# Phase 5A architecture-aware path remains available as --engine 0.2 (PHASE5A_ENGINE).
PHASE5A_ENGINE_VERSION = "0.2.0-dev"

# v0.1 result states (unchanged for baseline engine path)
RESULT_STATES = (
    "SEROVAR_CALL",
    "SEROVAR_5_OR_12",
    "MULTIPLE_SEROVAR_TARGETS",
    "NO_SEROVAR_TARGET",
    "INSUFFICIENT_TARGET_MATCH",
    "ERROR",
)

# Phase 4E retained primary result states + technical species/error states for v0.2
V02_RESULT_STATES = (
    "SUPPORTED_SEROVAR_ASSOCIATED_ARCHITECTURE",
    "SEROVAR_5_OR_12",
    "AMBIGUOUS_ARCHITECTURE",
    "ATYPICAL_CAPSULE_PROFILE",
    "INSUFFICIENT_CAPSULE_SEQUENCE",
    "ASSEMBLY_LIMITED",
    "CONFLICTING_GENOMIC_EVIDENCE",
    "NO_RECOGNIZED_CAPSULE_ARCHITECTURE",
    "SPECIES_CHECK_FAILED",
    "ERROR",
)

# Engineering defaults only for v0.1.1 path — not biologically validated cutoffs.
DEVELOPMENT_THRESHOLD_MIN_IDENTITY = 90.0
DEVELOPMENT_THRESHOLD_MIN_COVERAGE = 90.0
