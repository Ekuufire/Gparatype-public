"""Development defaults for Gparatype v0.2 (NOT biologically optimized).

SEARCH_* thresholds retain technical BLAST hits for architecture evidence.
DEVELOPMENT_DEFAULT_* values are labeling aids only — they are NOT probability
estimates and are NOT the v0.1.1 90/90 biological call rule.

v0.1.1 continues to use DEVELOPMENT_THRESHOLD_MIN_IDENTITY/COVERAGE = 90 for
its own path only (see gparatype.__init__).
"""

from __future__ import annotations

# --- Technical hit retention (SEARCH) ---
SEARCH_EVALUE = 1e-5
SEARCH_MIN_PIDENT = 70.0
SEARCH_MIN_QCOV = 50.0

# --- DEVELOPMENT labeling defaults (NOT call rules; NOT optimized) ---
DEVELOPMENT_DEFAULT_PRESENT_PIDENT = 90.0
DEVELOPMENT_DEFAULT_PRESENT_QCOV = 80.0
DEVELOPMENT_DEFAULT_PARTIAL_PIDENT = 70.0
DEVELOPMENT_DEFAULT_PARTIAL_QCOV = 50.0

# Competing architectures: absolute recovery_fraction difference band
DEVELOPMENT_DEFAULT_COMPETING_DELTA = 0.15

# Minimum fraction of expected components PRESENT/PARTIAL for "adequate content"
DEVELOPMENT_DEFAULT_MIN_CONTENT_SUPPORT = 0.50

# Species proxy: unique Howell CDS accessions with SEARCH-level hits
DEVELOPMENT_DEFAULT_SPECIES_OK_MIN = 5
DEVELOPMENT_DEFAULT_SPECIES_WEAK_MIN = 1

# Contig-edge NOT_OBSERVABLE window (bp)
DEVELOPMENT_DEFAULT_EDGE_BP = 500

# Diagnostic region labeling (descriptive only)
DEVELOPMENT_DEFAULT_DIAG_STRONG_PIDENT = 95.0
DEVELOPMENT_DEFAULT_DIAG_STRONG_QCOV = 90.0
DEVELOPMENT_DEFAULT_DIAG_MODERATE_PIDENT = 85.0
DEVELOPMENT_DEFAULT_DIAG_MODERATE_QCOV = 70.0
DEVELOPMENT_DEFAULT_DIAG_WEAK_PIDENT = 70.0
DEVELOPMENT_DEFAULT_DIAG_WEAK_QCOV = 50.0

DB_VERSION_DEFAULT = "GparatypeDB-2026.1-dev"
# Phase 5A frozen interpretation path (--engine 0.2)
SOFTWARE_ENGINE = "0.2"
PHASE5A_ENGINE = "0.2"
# Phase 5E hybrid interpretation path (--engine 0.2.1; CLI default)
HYBRID_ENGINE = "0.2.1"
HYBRID_ENGINE_VERSION = "0.2.1-dev"
