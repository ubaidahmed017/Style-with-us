#!/bin/bash
# Run the Style With Us test suites.
#
# Backend tests are infra-free by default (Pydantic validators, RBAC, firebase
# mocks). To also run the DB-backed integration test, export a Postgres DSN:
#   export STYLEWITHUS_TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/stylewithus_test

set -e

GREEN='\033[0;32m'
NC='\033[0m'

# Resolve repo root relative to this script (works on any machine).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}=== Style With Us Test Suite ===${NC}"

# --- Backend (pytest) ---
echo -e "\n${GREEN}Backend tests (pytest)...${NC}"
cd "$ROOT/backend"

# Prefer the project venv if present, else the system python.
PY="python"
[ -x ".venv/bin/python" ] && PY=".venv/bin/python"

"$PY" -m pytest -q

# --- Flutter (optional; requires the Flutter SDK) ---
if command -v flutter >/dev/null 2>&1; then
  echo -e "\n${GREEN}Flutter tests (flutter test)...${NC}"
  cd "$ROOT/FYP"
  flutter test
else
  echo -e "\n(Flutter SDK not found — skipping Flutter tests)"
fi

echo -e "\n${GREEN}=== Done ===${NC}"
