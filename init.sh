#!/usr/bin/env bash
# init.sh — Environment verification and initialization
#
# This script is run by the agent at the BEGINNING of a session and before
# declaring any task as `done`. If it fails, the session must not proceed.
#
# Expected output: clear exit codes and blocks marked with [OK]/[FAIL].

set -u
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
fail()  { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }

EXIT_CODE=0

# Detect python command (python3 on Linux/macOS, python on Windows)
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  fail "python3/python is not installed"
  exit 1
fi

echo "── 1. Verifying Python environment ─────────────────────"

ok "$PY -> $($PY --version)"

PY_VERSION_OK=$($PY -c 'import sys; print(int(sys.version_info >= (3, 11)))')
if [ "$PY_VERSION_OK" != "1" ]; then
  fail "Python >= 3.11 is required"
  exit 1
fi
ok "Compatible Python version"

if [ -d ".venv" ]; then
  ok ".venv/ exists"
  if [ -f ".venv/Scripts/python.exe" ] || [ -f ".venv/bin/python" ]; then
    ok "Virtualenv python found"
  else
    fail ".venv/ exists but has no python binary"
    EXIT_CODE=1
  fi
else
  warn ".venv/ not found — create with: python3 -m venv .venv"
fi

if [ -f "requirements.txt" ]; then
  ok "requirements.txt exists"
else
  fail "Missing requirements.txt"
  EXIT_CODE=1
fi

echo ""
echo "── 2. Verifying Node.js environment ────────────────────"

if ! command -v node >/dev/null 2>&1; then
  fail "node is not installed"
  EXIT_CODE=1
else
  ok "node -> $(node --version)"
fi

if ! command -v npm >/dev/null 2>&1; then
  fail "npm is not installed"
  EXIT_CODE=1
else
  ok "npm -> $(npm --version)"
fi

if [ -d "node_modules" ]; then
  ok "node_modules/ exists"
else
  warn "node_modules/ not found — run: npm install"
fi

if [ -f "package.json" ]; then
  ok "package.json exists"
else
  fail "Missing package.json"
  EXIT_CODE=1
fi

echo ""
echo "── 3. Verifying base harness files ─────────────────────"

for f in AGENTS.md feature_list.json progress/current.md progress/history.md \
         docs/architecture.md docs/conventions.md docs/verification.md \
         README.md; do
  if [ ! -f "$f" ]; then
    fail "Missing base file: $f"
    EXIT_CODE=1
  else
    ok "Exists $f"
  fi
done

for f in agents/leader.md agents/implementer.md agents/reviewer.md; do
  if [ ! -f "$f" ]; then
    warn "Missing agent file: $f"
  else
    ok "Exists $f"
  fi
done

echo ""
echo "── 4. Validating feature_list.json ─────────────────────"

$PY - <<'PY'
import json
import sys

try:
    data = json.load(open("feature_list.json"))
    valid = {"pending", "in_progress", "done", "blocked"}
    in_progress = [f for f in data["features"] if f["status"] == "in_progress"]

    if len(in_progress) > 1:
        print(f"[FAIL]  There are {len(in_progress)} features in in_progress (maximum 1)")
        sys.exit(1)

    for f in data["features"]:
        if f["status"] not in valid:
            print(f"[FAIL]  Invalid status in feature {f['id']}: {f['status']}")
            sys.exit(1)

    print(f"[OK]    feature_list.json is valid ({len(data['features'])} features)")
except Exception as e:
    print(f"[FAIL]  Invalid feature_list.json: {e}")
    sys.exit(1)
PY

if [ $? -ne 0 ]; then EXIT_CODE=1; fi

echo ""
echo "── 5. Running Python tests ──────────────────────────────"

if [ -d "tests" ]; then
  if $PY -m unittest discover -s tests -v 2>&1; then
    ok "All Python tests pass"
  else
    fail "Python tests are failing"
    EXIT_CODE=1
  fi
else
  warn "tests/ directory does not exist yet"
fi

echo ""
echo "── 6. Running frontend checks ──────────────────────────"

if [ -d "node_modules" ]; then
  if npm run lint >/dev/null 2>&1; then
    ok "npm run lint passes"
  else
    fail "npm run lint fails"
    EXIT_CODE=1
  fi

  if npm run build >/dev/null 2>&1; then
    ok "npm run build passes"
  else
    fail "npm run build fails"
    EXIT_CODE=1
  fi
else
  warn "Skipped frontend checks (node_modules/ missing)"
fi

echo ""
echo "── 7. Summary ──────────────────────────────────────────"

if [ $EXIT_CODE -eq 0 ]; then
  ok "Environment ready. You can start working."
else
  fail "Environment is NOT ready. Resolve the errors before proceeding."
fi

exit $EXIT_CODE
