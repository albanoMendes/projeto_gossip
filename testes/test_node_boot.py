import asyncio
import io

import pytest

from src.aplicacao.config import Member
from src.aplicacao.node import Node


def _members_with_ephemeral():
    # status/gossip ports 0 -> ephemeral; Node must rebind membership to the
    # actual bound ports after start.
    return {
        mid: Member(mid, "127.0.0.1", 0, 0)
        for mid in "ABCDEF"
    }


@pytest.mark.asyncio
async def test_node_boots_and_shuts_down_cleanly():
    members = _members_with_ephemeral()
    buf = io.StringIO()
    node = Node(
        node_id="A",
        members=members,
        interval=0.02,
        loss_probability=0.0,
        log_stream=buf,
    )
    await node.start()

    # Gossip and status endpoints are bound to real ports now.
    assert node.gossip_port > 0
    assert node.status_port > 0

    # Posting a notice via the CLI handler creates A:1 and logs CRIADO.
    node.post("hello")
    assert "A:1" in node.store.ids()
    assert "[A] CRIADO aviso=A:1" in buf.getvalue()

    # Let a few gossip cycles run (peers are not up, so sends just go nowhere).
    await asyncio.sleep(0.1)

    await node.stop()  # must not raise


@pytest.mark.asyncio
async def test_node_derives_five_peers_excluding_self():
    members = _members_with_ephemeral()
    node = Node("A", members, interval=0.02, loss_probability=0.0, log_stream=io.StringIO())
    await node.start()
    assert set(node.peers) == {"B", "C", "D", "E", "F"}
    await node.stop()
