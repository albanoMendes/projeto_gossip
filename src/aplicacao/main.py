# Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
"""Entry point for a single gossip node.

Usage:
    python -m src.aplicacao.main --id A [--config config/members.json]
                                 [--interval 0.3] [--fanout 2] [--loss 0.0]

Each process is started with its own ``--id`` and loads the full membership
(addresses and ports of A-F). The id determines the origin of locally created
notices and the exclusion of self in peer selection.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from src.aplicacao.config import load_members
from src.aplicacao.node import Node

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "members.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gossip bulletin-board node")
    parser.add_argument("--id", required=True, help="This node's id (A-F)")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to members config")
    parser.add_argument("--interval", type=float, default=0.3, help="Gossip interval (s)")
    parser.add_argument("--fanout", type=int, default=2, help="Peers contacted per cycle")
    parser.add_argument("--loss", type=float, default=0.0, help="Simulated loss probability")
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> None:
    members = load_members(args.config)
    if args.id not in members:
        raise SystemExit(f"unknown node id {args.id!r}; known: {sorted(members)}")

    node = Node(
        node_id=args.id,
        members=members,
        interval=args.interval,
        fanout=args.fanout,
        loss_probability=args.loss,
    )
    await node.start()
    node.start_cli()
    print(
        f"[{args.id}] node up: gossip={node.gossip_port} status={node.status_port} "
        f"interval={args.interval}s fanout={args.fanout} loss={args.loss}",
        flush=True,
    )
    print(f"[{args.id}] type 'post <texto>' to create a notice; Ctrl+C to stop.", flush=True)
    try:
        # Run forever (anti-entropy): the gossip cycle keeps going until killed.
        while True:
            await asyncio.sleep(3600)
    finally:
        await node.stop()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        print(f"\n[{args.id}] stopped (fail-stop).", flush=True)


if __name__ == "__main__":
    main()
