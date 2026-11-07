import asyncio
import socket

import pytest

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
async def test_malformed_bytes_do_not_crash_and_valid_message_still_handled():
    """RF-04.3 in practice: garbage to the gossip port must not kill the node;
    a subsequent valid GOSSIP must still be received and handled."""
    received: list[dict] = []

    receiver = UdpTransport(node_id="A", on_message=lambda msg, addr: received.append(msg))
    await receiver.start("127.0.0.1", 0)
    port = receiver.local_port

    # Send raw garbage straight to the gossip port with a plain UDP socket.
    raw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for payload in (b"garbage{{{", b"", b"\xff\xfe\xfa", b'{"partial": '):
        raw.sendto(payload, ("127.0.0.1", port))
    raw.close()

    # Give the loop a moment to process the garbage (all should be dropped).
    await asyncio.sleep(0.1)
    assert received == []

    # Now a valid message must still be handled -> node is alive.
    sender = UdpTransport(node_id="B", on_message=lambda msg, addr: None)
    await sender.start("127.0.0.1", 0)
    sender.send("127.0.0.1", port, {"type": "GOSSIP", "sender": "B", "notices": []})

    assert await _wait_for(lambda: len(received) == 1)
    assert received[0]["sender"] == "B"

    sender.close()
    receiver.close()
