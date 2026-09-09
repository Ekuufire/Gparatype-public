#!/usr/bin/env bash
# Public release verification — run from WSL; does NOT modify private repo.
set -euo pipefail
export PATH="/home/labstudent/anaconda3/bin:/usr/bin:/bin:${PATH:-}"

PRIVATE=/home/labstudent/Gparatype
PUBLIC=/home/labstudent/Gparatype-public
VENV=/tmp/gparatype-public-test-venv
REPORT=/tmp/gparatype_public_release_report.txt

: > "$REPORT"

log() { echo "$@" | tee -a "$REPORT"; }

log "=== Gparatype Public Release Verification ==="
log "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
log ""

# Private git HEAD before
PRIVATE_HEAD=""
if [ -d "$PRIVATE/.git" ]; then
  PRIVATE_HEAD=$(git -C "$PRIVATE" rev-parse HEAD 2>/dev/null || echo "none")
  log "Private repo HEAD (before): $PRIVATE_HEAD"
fi

# Checksum
CHK="$PUBLIC/data/gparatype_db/GparatypeDB-2026.1-freeze/checksums.sha256"
EXPECTED=b01061ccc091d3cfe1b42381aea0a1cf9f891e7bffce76f7ebcfe312fa34285a
GOT=$(sha256sum "$CHK" | awk '{print $1}')
log "Checksum checksums.sha256: $GOT (expected $EXPECTED)"
[ "$GOT" = "$EXPECTED" ]

# File size audit
log ""
log "=== File size audit ==="
TOTAL=$(du -sb "$PUBLIC" | awk '{print $1}')
log "Total bytes: $TOTAL ($(du -sh "$PUBLIC" | awk '{print $1}'))"
log "Largest 20 files:"
find "$PUBLIC" -type f -printf '%s %p\n' 2>/dev/null | sort -rn | head -20 | tee -a "$REPORT"
log ""
log "Files >10MB:"
find "$PUBLIC" -type f -size +10M -printf '%s %p\n' 2>/dev/null | tee -a "$REPORT" || true
log "Files >50MB:"
find "$PUBLIC" -type f -size +50M -printf '%s %p\n' 2>/dev/null | tee -a "$REPORT" || true
log "Files >100MB:"
find "$PUBLIC" -type f -size +100M -printf '%s %p\n' 2>/dev/null | tee -a "$REPORT" || true

# Security audit (simple patterns)
log ""
log "=== Security audit (pattern scan) ==="
SECRETS=0
if rg -i 'password|api_key|secret|token|credential|id_rsa' "$PUBLIC" --glob '!*.pyc' -g '!data/gparatype_db/**' 2>/dev/null; then
  SECRETS=1
fi
if [ "$SECRETS" -eq 0 ]; then
  log "No obvious secret patterns in code/docs (excluding DB provenance DOI fields)."
else
  log "WARNING: review pattern matches above."
fi

# Fresh venv install
log ""
log "=== Install test ==="
rm -rf "$VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q -e "$PUBLIC[dev]"
log "gparatype --help:"
gparatype --help | head -5 | tee -a "$REPORT"
log "gparatype --version:"
gparatype --version 2>&1 | tee -a "$REPORT"
log "blastn -version:"
blastn -version 2>&1 | head -1 | tee -a "$REPORT" || log "blastn not on PATH"
log "gparatype.__file__:"
python3 -c "import gparatype; print(gparatype.__file__)" | tee -a "$REPORT"
python3 -c "
from gparatype.v02.database import default_database_path
p = default_database_path()
print('default_database_path:', p)
assert 'freeze' in p.name and 'dev' not in p.name
" | tee -a "$REPORT"
log "pytest:"
cd "$PUBLIC"
pytest -q 2>&1 | tee -a "$REPORT"

# Git init public only
log ""
log "=== Git init (public only) ==="
cd "$PUBLIC"
if [ ! -d .git ]; then
  git init -b main
  git config user.email "gparatype-public@research.local"
  git config user.name "Gparatype Public Release"
  git add -A
  git commit -m "Initial public research release of Gparatype v0.2.1"
  log "Created initial commit: $(git rev-parse HEAD)"
elif ! git rev-parse HEAD >/dev/null 2>&1; then
  git config user.email "gparatype-public@research.local"
  git config user.name "Gparatype Public Release"
  git add -A
  git commit -m "Initial public research release of Gparatype v0.2.1"
  log "Created initial commit: $(git rev-parse HEAD)"
else
  log "Git already initialized: $(git rev-parse HEAD)"
fi
log "No remote configured: $(git remote 2>/dev/null | wc -l) remotes"

# Private git HEAD after
if [ -d "$PRIVATE/.git" ]; then
  PRIVATE_HEAD_AFTER=$(git -C "$PRIVATE" rev-parse HEAD 2>/dev/null || echo "none")
  log "Private repo HEAD (after): $PRIVATE_HEAD_AFTER"
  if [ "$PRIVATE_HEAD" = "$PRIVATE_HEAD_AFTER" ]; then
    log "Private repo HEAD unchanged: OK"
  else
    log "WARNING: Private repo HEAD changed!"
  fi
fi

log ""
log "=== DONE ==="
log "Report: $REPORT"
