import pytest

from testes.e2e_helpers import start_cluster, stop_cluster, wait_until


@pytest.mark.asyncio
async def test_convergence_under_moderate_loss():
    """CA-05: with ~30% message loss, all nodes still converge given enough
    cycles. Anti-entropy repairs losses through subsequent periodic exchanges
    and alternative propagation paths (no directed retransmission)."""
    nodes = await start_cluster(interval=0.01, loss_probability=0.3, seed=42)
    try:
        nodes["A"].post("resilient notice")
        converged = await wait_until(
            lambda: all(nodes[n].store.ids() == {"A:1"} for n in "ABCDEF"),
            timeout=8.0,  # generous budget to avoid flakiness under loss
        )
        assert converged, {n: sorted(nodes[n].store.ids()) for n in "ABCDEF"}
    finally:
        await stop_cluster(nodes)
