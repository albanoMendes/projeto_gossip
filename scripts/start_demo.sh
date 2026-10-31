#!/usr/bin/env bash
# Start the full demo: six gossip nodes (A-F) + the observer panel.
#
# tmux mode gives each node its own interactive pane so you can type
# `post <texto>` into any node and kill a node with Ctrl+C (fail-stop).
# background mode runs the processes with per-node log files in ./evidencias/
# (stdin is not interactive there, so `post` is unavailable).
#
# Usage:
#   scripts/start_demo.sh [mode] [interval] [loss]
#     mode     : tmux | background | auto   (default: auto -> tmux if available)
#     interval : gossip interval in seconds (default: 0.3)
#     loss     : simulated loss probability (default: 0.0)
# Examples:
#   scripts/start_demo.sh                 # auto, interval=0.3, loss=0.0
#   scripts/start_demo.sh tmux            # force tmux
#   scripts/start_demo.sh background      # force background + logs
#   scripts/start_demo.sh tmux 0.3 0.3    # tmux, 30% message loss
#   scripts/start_demo.sh 0.3 0.3         # back-compat: numeric 1st arg = interval

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Parse optional leading mode. If the first arg is numeric, treat it as interval
# (backward compatible with the old `start_demo.sh [interval] [loss]` form).
MODE="auto"
case "${1:-}" in
  tmux|background|auto) MODE="$1"; shift ;;
esac

INTERVAL="${1:-0.3}"
LOSS="${2:-0.0}"
NODES=(A B C D E F)

# Pick the Python interpreter: prefer the project venv if present.
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="python3"
fi

SESSION="gossip"

# Resolve auto -> tmux if available, else background.
if [[ "$MODE" == "auto" ]]; then
  if command -v tmux >/dev/null 2>&1; then MODE="tmux"; else MODE="background"; fi
fi

if [[ "$MODE" == "tmux" ]]; then
  if ! command -v tmux >/dev/null 2>&1; then
    echo "ERROR: tmux mode requested but tmux is not installed." >&2
    echo "Install tmux or use: scripts/start_demo.sh background" >&2
    exit 1
  fi
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  tmux new-session -d -s "$SESSION" -n nodes

  # First node in the initial pane.
  tmux send-keys -t "$SESSION":0 \
    "$PY -m src.aplicacao.main --id A --interval $INTERVAL --loss $LOSS" C-m

  # Remaining nodes, each in a new split pane.
  for id in B C D E F; do
    tmux split-window -t "$SESSION":0
    tmux select-layout -t "$SESSION":0 tiled >/dev/null
    tmux send-keys -t "$SESSION":0 \
      "$PY -m src.aplicacao.main --id $id --interval $INTERVAL --loss $LOSS" C-m
  done

  # Panel in its own window.
  tmux new-window -t "$SESSION" -n panel
  tmux send-keys -t "$SESSION":panel \
    "$PY -m src.monitoramento.panel_main --interval 1.0" C-m

  echo "tmux session '$SESSION' started."
  echo "Attach with:  tmux attach -t $SESSION"
  echo "  window 'nodes' : A-F (type 'post <texto>' in any pane; Ctrl+C to kill a node)"
  echo "  window 'panel' : observer panel"
  echo "Stop everything with:  scripts/stop_demo.sh"
else
  echo "Starting background processes with log files in ./evidencias/"
  mkdir -p evidencias
  : > evidencias/pids.txt
  for id in "${NODES[@]}"; do
    "$PY" -m src.aplicacao.main --id "$id" --interval "$INTERVAL" --loss "$LOSS" \
      > "evidencias/node_${id}.log" 2>&1 &
    echo $! >> evidencias/pids.txt
  done
  "$PY" -m src.monitoramento.panel_main --interval 1.0 \
    > evidencias/panel.log 2>&1 &
  echo $! >> evidencias/pids.txt
  echo "Started 6 nodes + panel in background. Logs: ./evidencias/*.log"
  echo "NOTE: in background mode stdin is not interactive, so 'post' is unavailable."
  echo "      Use tmux mode for the interactive demo. Stop with: scripts/stop_demo.sh"
fi
