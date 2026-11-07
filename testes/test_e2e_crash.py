import pytest

from src.monitoramento.panel import Panel
from testes.e2e_helpers import start_cluster, stop_cluster, wait_until


@pytest.mark.asyncio
async def test_remaining_nodes_converge_after_one_crashes():
    """CA-06: after F is killed, A-E keep gossiping and converge among
    themselves. F simply stops; there is no failure detector."""
    nodes = await start_cluster(interval=0.01, loss_probability=0.0, seed=7)
    try:
        # Kill F (fail-stop): close its endpoints and stop its loop.
        await nodes["F"].stop()

        nodes["A"].post("after crash")
        survivors = "ABCDE"
        converged = await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1"} for n in survivors),
            timeout=6.0,
        )
        assert converged, {n: sorted(nodes[n].store.ids()) for n in survivors}
    finally:
        # Stop the survivors (F already stopped).
        for n in "ABCDE":
            await nodes[n].stop()


@pytest.mark.asyncio
async def test_panel_marks_crashed_node_unavailable():
    """CA-06 (observer): the panel shows the stopped node as unavailable while
    reporting coverage over the active nodes."""
    nodes = await start_cluster(interval=0.01, loss_probability=0.0, seed=8)
    try:
        await nodes["F"].stop()
        nodes["A"].post("x")
        await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1"} for n in "ABCDE"),
            timeout=6.0,
        )

        # Build a panel pointed at the real status ports of all six members.
        from src.aplicacao.config import Member

        members = {
            n: Member(n, "127.0.0.1", nodes[n].gossip_port, nodes[n].status_port)
            for n in "ABCDE"
        }
        # F is down: point its status port at one nothing listens on, so the
        # panel query times out and marks it unavailable.
        members["F"] = Member("F", "127.0.0.1", 0, 1)

        panel = Panel(members, timeout=0.2)
        snapshot = await panel.collect()
        assert snapshot["F"] is None  # unavailable
        assert snapshot["A"] == {"A:1"}
    finally:
        for n in "ABCDE":
            await nodes[n].stop()
