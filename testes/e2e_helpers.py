"""Shared helpers for end-to-end tests that boot real UDP nodes on loopback."""

from __future__ import annotations

import asyncio
import io
import random

from src.aplicacao.config import Member
from src.aplicacao.node import Node


def ephemeral_members(ids="ABCDEF") -> dict[str, Member]:
    """Members with port 0 so each node binds to ephemeral ports."""
    return {mid: Member(mid, "127.0.0.1", 0, 0) for mid in ids}


async def start_cluster(
    ids="ABCDEF",
    interval: float = 0.02,
    loss_probability: float = 0.0,
    seed: int = 0,
) -> dict[str, Node]:
    """Boot a cluster of nodes and cross-wire their real (ephemeral) ports.

    Nodes are created and bound first; then every node's engine membership is
    rebuilt so ids map to the actual bound gossip ports of all peers.
    """
    members = ephemeral_members(ids)
    nodes: dict[str, Node] = {}
    for i, mid in enumerate(members):
        nodes[mid] = Node(
            node_id=mid,
            members=members,
            interval=interval,
            loss_probability=loss_probability,
            rng=random.Random(seed + i),
            log_stream=io.StringIO(),
        )
    for node in nodes.values():
        await node.start()

    # Build the real id -> (host, gossip_port) map from bound ports.
    real = {mid: ("127.0.0.1", nodes[mid].gossip_port) for mid in nodes}
    for node in nodes.values():
        node._engine.attach_transport(node._transport, real)
    return nodes


async def stop_cluster(nodes: dict[str, Node]) -> None:
    for node in nodes.values():
        await node.stop()


async def wait_until(predicate, timeout: float = 5.0, interval: float = 0.02) -> bool:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(interval)
    return predicate()
