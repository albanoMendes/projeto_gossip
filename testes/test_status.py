import asyncio
import socket

import pytest

from src.comunicacao import codec
from src.estado.store import NoticeStore
from src.monitoramento.status_server import StatusServer


async def _request_status(host, port, timeout=1.0):
    """Send a STATUS_REQUEST over UDP and return the decoded reply (or None)."""
    loop = asyncio.get_event_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    try:
        req = codec.encode({"type": "STATUS_REQUEST", "sender": "panel"})
        sock.sendto(req, (host, port))
        fut = loop.sock_recv(sock, 65535)
        data = await asyncio.wait_for(fut, timeout=timeout)
        return codec.decode(data)
    finally:
        sock.close()


@pytest.mark.asyncio
async def test_status_reply_contains_store_ids():
    store = NoticeStore(origem="A")
    store.add_local("mine")  # A:1

    server = StatusServer(node_id="A", store=store)
    await server.start("127.0.0.1", 0)

    reply = await _request_status("127.0.0.1", server.local_port)
    assert reply is not None
    assert reply["type"] == "STATUS_REPLY"
    assert reply["sender"] == "A"
    assert set(reply["notices"]) == {"A:1"}

    server.close()


@pytest.mark.asyncio
async def test_status_request_does_not_mutate_store():
    store = NoticeStore(origem="A")
    store.add_local("mine")
    before = store.ids()

    server = StatusServer(node_id="A", store=store)
    await server.start("127.0.0.1", 0)

    await _request_status("127.0.0.1", server.local_port)
    await _request_status("127.0.0.1", server.local_port)

    assert store.ids() == before  # read-only

    server.close()


@pytest.mark.asyncio
async def test_status_server_ignores_malformed_without_crashing():
    store = NoticeStore(origem="A")
    store.add_local("mine")

    server = StatusServer(node_id="A", store=store)
    await server.start("127.0.0.1", 0)
    port = server.local_port

    raw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    raw.sendto(b"garbage{{{", ("127.0.0.1", port))
    raw.close()
    await asyncio.sleep(0.05)

    # Still answers a valid request afterward.
    reply = await _request_status("127.0.0.1", port)
    assert reply is not None and reply["type"] == "STATUS_REPLY"

    server.close()
