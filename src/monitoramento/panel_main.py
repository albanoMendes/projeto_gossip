"""Entry point for the observer panel (RF-12).

Periodically queries every node's status port (read-only) and prints a textual
table of which nodes know each notice, plus the observed coverage over the
active nodes. The panel never participates in gossip; killing it does not affect
the nodes.

Usage:
    python -m src.monitoramento.panel_main [--config config/members.json]
                                           [--interval 1.0] [--timeout 0.2]
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from src.aplicacao.config import load_members
from src.monitoramento.panel import Panel, all_known_ids, render_panel

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "members.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gossip observer panel")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--interval", type=float, default=1.0, help="Refresh interval (s)")
    parser.add_argument("--timeout", type=float, default=0.2, help="Per-query timeout (s)")
    return parser.parse_args(argv)


def render_snapshot(snapshot) -> str:
    """Render the full panel: one table per known notice, or a hint if empty."""
    known = sorted(all_known_ids(snapshot))
    active = sum(1 for ids in snapshot.values() if ids is not None)
    blocks = [f"=== PAINEL (observador) — {active} nó(s) ativo(s) ==="]
    if not known:
        blocks.append("Nenhum aviso observado ainda.")
    else:
        for notice_id in known:
            blocks.append(render_panel(notice_id, snapshot))
    return "\n\n".join(blocks)


async def _run(args: argparse.Namespace) -> None:
    members = load_members(args.config)
    panel = Panel(members, timeout=args.timeout)
    while True:
        snapshot = await panel.collect()
        print("\033[2J\033[H", end="")  # clear screen
        print(render_snapshot(snapshot), flush=True)
        await asyncio.sleep(args.interval)


def main(argv: list[str] | None = None) -> None:
    try:
        asyncio.run(_run(parse_args(argv)))
    except KeyboardInterrupt:
        print("\n[panel] encerrado.", flush=True)


if __name__ == "__main__":
    main()
