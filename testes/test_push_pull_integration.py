import asyncio

import pytest

from src.comunicacao.transport import UdpTransport
from src.estado.store import NoticeStore
from src.gossip.engine import GossipEngine


async def _wait_for(predicate, timeout=1.5, interval=0.01):
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(interval)
    return predicate()


def _dispatch(engine):
    """Return an on_message callback routing GOSSIP/REPLY to the engine."""

    def handler(message, addr):
        if message.get("type") == "GOSSIP":
            engine.handle_gossip(message)
        elif message.get("type") == "REPLY":
            engine.handle_reply(message)

    return handler


@pytest.mark.asyncio
async def test_two_real_nodes_converge_to_union_after_push_pull():
    """CA-08 over real UDP on 127.0.0.1: one push-pull exchange leaves both
    stores holding the union of A's and B's notices, with no loss."""
    store_a = NoticeStore(origem="A")
    store_a.add_local("a1")  # A:1
    store_b = NoticeStore(origem="B")
    store_b.add_local("b1")  # B:1

    # Engines are created first; transports are injected after we know the ports.
    engine_a = GossipEngine("A", store_a, transport=None, members={})
    engine_b = GossipEngine("B", store_b, transport=None, members={})

    transport_a = UdpTransport("A", on_message=_dispatch(engine_a))
    transport_b = UdpTransport("B", on_message=_dispatch(engine_b))
    await transport_a.start("127.0.0.1", 0)
    await transport_b.start("127.0.0.1", 0)

    members = {
        "A": ("127.0.0.1", transport_a.local_port),
        "B": ("127.0.0.1", transport_b.local_port),
    }
    # Inject transport + membership now that ports are known.
    engine_a.attach_transport(transport_a, members)
    engine_b.attach_transport(transport_b, members)

    # A initiates the push-pull exchange toward B.
    engine_a.send_gossip("B")

    assert await _wait_for(
        lambda: store_a.ids() == {"A:1", "B:1"} and store_b.ids() == {"A:1", "B:1"}
    )

    transport_a.close()
    transport_b.close()
