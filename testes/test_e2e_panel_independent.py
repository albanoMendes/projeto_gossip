import asyncio

import pytest

from src.aplicacao.config import Member
from src.monitoramento.panel import Panel
from testes.e2e_helpers import start_cluster, stop_cluster, wait_until


@pytest.mark.asyncio
async def test_gossip_continues_after_panel_stops():
    """CA-07: the panel is a read-only observer. Starting and then abandoning
    it (simulating a crash) must not affect gossip: nodes keep converging."""
    nodes = await start_cluster(interval=0.01, loss_probability=0.0, seed=9)
    try:
        members = {
            n: Member(n, "127.0.0.1", nodes[n].gossip_port, nodes[n].status_port)
            for n in "ABCDEF"
        }
        panel = Panel(members, timeout=0.2)

        # Panel observes once, then "dies" (we stop querying entirely).
        await panel.collect()
        del panel  # observer gone

        # Gossip must still converge with no observer present.
        nodes["A"].post("notice after panel death")
        converged = await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1"} for n in "ABCDEF"),
            timeout=5.0,
        )
        assert converged, {n: sorted(nodes[n].store.ids()) for n in "ABCDEF"}
    finally:
        await stop_cluster(nodes)


@pytest.mark.asyncio
async def test_panel_query_is_read_only_and_does_not_disturb_state():
    """Querying status repeatedly must not change what the nodes know."""
    nodes = await start_cluster(interval=0.01, loss_probability=0.0, seed=10)
    try:
        nodes["A"].post("x")
        await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1"} for n in "ABCDEF"),
            timeout=5.0,
        )
        members = {
            n: Member(n, "127.0.0.1", nodes[n].gossip_port, nodes[n].status_port)
            for n in "ABCDEF"
        }
        panel = Panel(members, timeout=0.2)
        for _ in range(5):
            snapshot = await panel.collect()
            await asyncio.sleep(0.02)
        assert all(snapshot[n] == {"A:1"} for n in "ABCDEF")
    finally:
        await stop_cluster(nodes)
