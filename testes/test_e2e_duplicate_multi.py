import pytest

from testes.e2e_helpers import start_cluster, stop_cluster, wait_until


@pytest.mark.asyncio
async def test_repeated_reception_does_not_duplicate():
    """CA-03: receiving the same notice many times never duplicates it."""
    nodes = await start_cluster(interval=0.01, loss_probability=0.0, seed=3)
    try:
        nodes["A"].post("hello")
        converged = await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1"} for n in "ABCDEF"),
            timeout=5.0,
        )
        assert converged
        # Let many more cycles run; the notice keeps circulating but is deduped.
        import asyncio

        await asyncio.sleep(0.3)
        for n in "ABCDEF":
            ids = nodes[n].store.ids()
            assert ids == {"A:1"}
            # Exactly one notice object per id (store is keyed by id).
            assert len(nodes[n].store.all()) == 1
    finally:
        await stop_cluster(nodes)


@pytest.mark.asyncio
async def test_notices_from_different_origins_both_propagate():
    """CA-04: notices created in A and B both end up in every node's set."""
    nodes = await start_cluster(interval=0.01, loss_probability=0.0, seed=4)
    try:
        nodes["A"].post("from A")  # A:1
        nodes["B"].post("from B")  # B:1
        converged = await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1", "B:1"} for n in "ABCDEF"),
            timeout=5.0,
        )
        assert converged, {n: sorted(nodes[n].store.ids()) for n in "ABCDEF"}
    finally:
        await stop_cluster(nodes)
