#!/usr/bin/env bash
# install-hooks.sh — point git at the hooks this repo ships.
#
#   bash scripts/install-hooks.sh
#
# Uses core.hooksPath rather than copying into .git/hooks, so the hooks are
# versioned with the code and a fresh clone picks up later changes to them
# without anyone re-running an installer.
#
# Run it once per clone. It is safe to run again.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/hooks/*
git config core.hooksPath scripts/hooks

echo "core.hooksPath -> scripts/hooks"
echo "installed:"
for h in scripts/hooks/*; do
  [ -f "$h" ] && echo "  $(basename "$h")"
done
echo
echo "To bypass once (and you should have a reason): git commit --no-verify"
