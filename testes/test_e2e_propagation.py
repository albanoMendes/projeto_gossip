import pytest

from testes.e2e_helpers import start_cluster, stop_cluster, wait_until


@pytest.mark.asyncio
async def test_notice_created_in_a_starts_only_in_a():
    """CA-01: a notice created in A appears initially only in A."""
    nodes = await start_cluster(interval=0.02, loss_probability=0.0, seed=1)
    try:
        nodes["A"].post("seminar at 10h")
        # Immediately after posting, only A knows it.
        assert nodes["A"].store.ids() == {"A:1"}
        assert all(nodes[n].store.ids() == set() for n in "BCDEF")
    finally:
        await stop_cluster(nodes)


@pytest.mark.asyncio
async def test_notice_propagates_to_all_six_nodes():
    """CA-02: with no loss, all six nodes eventually learn the notice."""
    nodes = await start_cluster(interval=0.02, loss_probability=0.0, seed=2)
    try:
        nodes["A"].post("seminar at 10h")
        converged = await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1"} for n in "ABCDEF"),
            timeout=5.0,
        )
        assert converged, {n: sorted(nodes[n].store.ids()) for n in "ABCDEF"}
    finally:
        await stop_cluster(nodes)
