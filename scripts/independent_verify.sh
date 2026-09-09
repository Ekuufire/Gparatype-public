#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/labstudent/anaconda3/bin:/usr/bin:/bin:${PATH:-}"
PRIVATE=/home/labstudent/Gparatype
PUBLIC=/home/labstudent/Gparatype-public
VENV="/tmp/gparatype-public-verify-$$"
REPORT="/tmp/gparatype_independent_verify_report.txt"
: > "$REPORT"

section() { echo ""; echo "=== $1 ==="; echo "=== $1 ===" >> "$REPORT"; }

run() {
  echo "+ $*"
  echo "+ $*" >> "$REPORT"
  { eval "$@" 2>&1 || true; } | tee -a "$REPORT"
}

section "A. Private source repository status"
run "git -C '$PRIVATE' status -sb"
run "git -C '$PRIVATE' rev-parse HEAD"
run "git -C '$PRIVATE' diff --stat"

section "B. Private HEAD and tag v0.2.1-research-freeze"
run "git -C '$PRIVATE' rev-parse HEAD"
run "git -C '$PRIVATE' rev-parse v0.2.1-research-freeze 2>&1"
run "git -C '$PRIVATE' show v0.2.1-research-freeze --no-patch --format='%H %s' 2>&1"

section "C. Public distribution path exists"
run "ls -ld '$PUBLIC'"

section "D. Public git"
run "git -C '$PUBLIC' rev-parse HEAD"
run "git -C '$PUBLIC' log -1"
run "git -C '$PUBLIC' remote -v"
run "git -C '$PUBLIC' status -sb"

section "E. Public package version"
run "grep -E '^version' '$PUBLIC/pyproject.toml'"
run "grep '__version__' '$PUBLIC/src/gparatype/__init__.py'"

section "F. Hybrid default engine 0.2.1 in cli"
run "grep -n 'default=\"0.2.1\"' '$PUBLIC/src/gparatype/cli.py'"
run "grep -n 'choices=\[\"0.2.1\"' '$PUBLIC/src/gparatype/cli.py'"

section "G. Runtime files under src and data"
run "find '$PUBLIC/src' -type f | sort"
run "find '$PUBLIC/data' -type f | sort"

section "H. Excluded items check"
run "find '$PUBLIC' -path '*/GparatypeDB-2026.1-dev*' 2>/dev/null | head -20"
run "find '$PUBLIC' -name '*.ipynb' 2>/dev/null | head -20"
run "find '$PUBLIC' \\( -path '*validation_genomes*' -o -path '*phase5*genomes*' -o -path '*/results/*' \\) 2>/dev/null | head -20"

section "I. Frozen DB included path"
run "ls -ld '$PUBLIC/data/gparatype_db/GparatypeDB-2026.1-freeze'"

section "J. checksums.sha256 hash"
run "sha256sum '$PUBLIC/data/gparatype_db/GparatypeDB-2026.1-freeze/checksums.sha256'"

section "K. Database directory size"
run "du -sh '$PUBLIC/data/gparatype_db/GparatypeDB-2026.1-freeze'"

section "L. Total Gparatype-public size"
run "du -sh '$PUBLIC'"
run "git -C '$PUBLIC' ls-files -z | xargs -0 -I{} du -ch '$PUBLIC/{}' 2>/dev/null | tail -1"

section "M. Largest 20 files"
run "du -ah '$PUBLIC' 2>/dev/null | sort -hr | head -20"
run "find '$PUBLIC' -type f -size +10M -printf '%s %p\n' 2>/dev/null"
run "find '$PUBLIC' -type f -size +50M -printf '%s %p\n' 2>/dev/null"
run "find '$PUBLIC' -type f -size +100M -printf '%s %p\n' 2>/dev/null"

section "N. Python requirements from pyproject"
run "cat '$PUBLIC/pyproject.toml'"

section "O. System requirements blastn"
run "which blastn 2>&1"
run "blastn -version 2>&1 | head -1"

section "P-Q. Fresh venv install and gparatype from /tmp"
rm -rf "$VENV"
run "python3 -m venv '$VENV'"
run "source '$VENV/bin/activate' && pip install -q '$PUBLIC' && cd /tmp && gparatype --help | head -8"
run "source '$VENV/bin/activate' && cd /tmp && gparatype --version 2>&1"
run "source '$VENV/bin/activate' && cd /tmp && python3 -c \"import gparatype; print(gparatype.__file__); from gparatype.v02.database import default_database_path; print(default_database_path())\""

section "R. Example workflow"
echo "Full genome analysis: NOT RUN (verification used --help/--version only from /tmp cwd)" | tee -a "$REPORT"

section "S. pytest"
run "cd '$PUBLIC' && pytest -q"

section "T. Independence checks"
run "source '$VENV/bin/activate' && cd /tmp && env -u PYTHONPATH python3 -c \"import gparatype; from gparatype.v02.database import default_database_path; print('file', gparatype.__file__); print('db', default_database_path())\""
run "grep -R '/home/labstudent/Gparatype[^-]' '$PUBLIC/src' 2>/dev/null || echo 'NO private absolute paths in src'"
run "grep -R '/home/labstudent/Gparatype[^-]' '$PUBLIC/docs' '$PUBLIC/tests' '$PUBLIC/README.md' 2>/dev/null || echo 'NO private absolute paths in docs/tests/readme'"

section "U. Absolute runtime paths labstudent in public tree"
run "grep -R 'labstudent' '$PUBLIC' --include='*.py' --include='*.md' --include='*.toml' --include='*.yml' --include='*.cff' --include='*.txt' --include='*.sh' 2>/dev/null || echo 'none'"

section "V. Security scan"
SECRETS=0
if rg -i 'password|api_key|secret|token|credential|id_rsa' "$PUBLIC" --glob '!*.pyc' -g '!data/gparatype_db/**' -g '!.git/**' 2>/dev/null; then SECRETS=1; fi
if [ "$SECRETS" -eq 0 ]; then echo "No obvious secret patterns in code/docs (excluding DB provenance)." | tee -a "$REPORT"; fi

section "W. Docs exist"
run "ls -1 '$PUBLIC/README.md' '$PUBLIC/CITATION.cff' '$PUBLIC/docs/'"

section "X. License files"
run "test ! -f '$PUBLIC/LICENSE' && echo 'NO LICENSE file (expected)'"
run "test -f '$PUBLIC/docs/LICENSE_DECISION_REQUIRED.md' && echo 'LICENSE_DECISION_REQUIRED.md exists'"

section "Gitignore / tracked artifacts"
run "cat '$PUBLIC/.gitignore'"
run "git -C '$PUBLIC' ls-files | grep -E 'pytest_cache|egg-info|__pycache__|build/' || echo 'No cache/egg-info/build tracked in git'"

section "Y-Z blockers and verdict"
echo "See report for blockers" | tee -a "$REPORT"
echo "REPORT_PATH=$REPORT"
