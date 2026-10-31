#!/usr/bin/env bash
# Stop the demo started by start_demo.sh (tmux session or background processes).

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SESSION="gossip"

if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux kill-session -t "$SESSION"
  echo "tmux session '$SESSION' killed."
fi

if [[ -f evidencias/pids.txt ]]; then
  while read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < evidencias/pids.txt
  rm -f evidencias/pids.txt
  echo "Background demo processes stopped."
fi

echo "Done."
