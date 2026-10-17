#!/usr/bin/env bash
# Verify that the incident branch passes tests.
# Usage: verify-recovery.sh [branch]
# If no branch is given, uses the current branch.
set -euo pipefail

branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"
echo "verifying recovery on branch: $branch"

git checkout "$branch"

cd backend
uv run pytest
cd ..

cd frontend
npm test
cd ..

echo "PASS"
