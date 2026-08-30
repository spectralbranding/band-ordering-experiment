#!/usr/bin/env bash
# reproduce.sh — single-command reproduction of the band-ordering experiment.
#
# Recomputes every number in the README from scratch and regenerates the figure.
# Deterministic: seed 20260830. A second run is byte-identical to the first.
#
# Usage:
#   ./reproduce.sh                  # full 10-seed study, then the figure
#   ./reproduce.sh --check-only     # verify dependencies only, run nothing
#
# Runtime is roughly 40 minutes on a laptop. Output is teed to output/logs/.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

mkdir -p output/figures output/logs
LOG_FILE="output/logs/master_run.log"

command -v uv >/dev/null 2>&1 || {
  echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
}

if [[ "${1:-}" == "--check-only" ]]; then
  echo "uv found. Dependencies are declared inline (PEP 723); nothing else is needed."
  exit 0
fi

{
  echo "=== band-ordering-experiment: run started $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  uv run --script code/band_ordering_study.py
  uv run --script code/make_figure.py
  echo "=== run complete $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
} 2>&1 | tee "$LOG_FILE"
