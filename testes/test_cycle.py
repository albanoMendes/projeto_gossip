import asyncio
import random

import pytest

from src.estado.store import NoticeStore
from src.gossip.engine import GossipEngine
from src.gossip.peer_selector import PeerSelector


class FakeTransport:
    def __init__(self):
        self.sent = []

    def send(self, host, port, message):
        self.sent.append((host, port, message))


def _members():
    return {
        "A": ("127.0.0.1", 5001),
        "B": ("127.0.0.1", 5002),
        "C": ("127.0.0.1", 5003),
        "D": ("127.0.0.1", 5004),
        "E": ("127.0.0.1", 5005),
        "F": ("127.0.0.1", 5006),
    }


def _engine():
    store = NoticeStore(origem="A")
    store.add_local("mine")
    transport = FakeTransport()
    selector = PeerSelector(["B", "C", "D", "E", "F"], fanout=2, rng=random.Random(5))
    engine = GossipEngine("A", store, transport, _members(), selector=selector)
    return engine, transport


def test_one_cycle_sends_two_gossip_to_two_distinct_peers():
    engine, transport = _engine()
    engine.run_one_cycle()

    assert len(transport.sent) == 2
    assert all(msg["type"] == "GOSSIP" for _, _, msg in transport.sent)
    dests = {port for _, port, _ in transport.sent}
    assert len(dests) == 2  # two distinct peers


@pytest.mark.asyncio
async def test_cycle_loop_runs_multiple_cycles_until_stopped():
    engine, transport = _engine()
    task = asyncio.create_task(engine.run_cycle_loop(interval=0.01))
    await asyncio.sleep(0.05)
    engine.stop()
    await task

    # At ~10ms interval over ~50ms we expect several cycles, 2 sends each.
    assert len(transport.sent) >= 4
    assert len(transport.sent) % 2 == 0
