import asyncio
import random

import pytest

from src.comunicacao.loss import LossSimulator
from src.comunicacao.transport import UdpTransport


async def _wait_for(predicate, timeout=1.0, interval=0.01):
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(interval)
    return predicate()


@pytest.mark.asyncio
async def test_loopback_delivers_message():
    received: list[dict] = []

    receiver = UdpTransport(node_id="B", on_message=lambda msg, addr: received.append(msg))
    await receiver.start("127.0.0.1", 0)
    port = receiver.local_port

    sender = UdpTransport(node_id="A", on_message=lambda msg, addr: None)
    await sender.start("127.0.0.1", 0)

    sender.send("127.0.0.1", port, {"type": "GOSSIP", "sender": "A", "notices": []})

    assert await _wait_for(lambda: len(received) == 1)
    assert received[0]["type"] == "GOSSIP"
    assert received[0]["sender"] == "A"

    sender.close()
    receiver.close()


@pytest.mark.asyncio
async def test_full_loss_delivers_nothing():
    received: list[dict] = []

    receiver = UdpTransport(node_id="B", on_message=lambda msg, addr: received.append(msg))
    await receiver.start("127.0.0.1", 0)
    port = receiver.local_port

    loss = LossSimulator(1.0, rng=random.Random(1))
    sender = UdpTransport(node_id="A", on_message=lambda msg, addr: None, loss=loss)
    await sender.start("127.0.0.1", 0)

    for _ in range(20):
        sender.send("127.0.0.1", port, {"type": "GOSSIP", "sender": "A", "notices": []})

    await asyncio.sleep(0.2)
    assert received == []

    sender.close()
    receiver.close()
