"""Read-only status server for the observer panel (RF-12).

A separate asyncio DatagramProtocol bound to the node's dedicated status port.
It answers STATUS_REQUEST with a STATUS_REPLY carrying only the ids of the
known notices. It never mutates the store and never participates in gossip, so
the observer stays strictly read-only.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.comunicacao import codec
from src.estado.store import NoticeStore


class _StatusProtocol(asyncio.DatagramProtocol):
    def __init__(self, node_id: str, store: NoticeStore) -> None:
        self._node_id = node_id
        self._store = store
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        message = codec.decode(data)
        if message is None or message.get("type") != "STATUS_REQUEST":
            # Drop malformed or unexpected datagrams without crashing.
            return
        reply = {
            "type": "STATUS_REPLY",
            "sender": self._node_id,
            "notices": sorted(self._store.ids()),
        }
        assert self.transport is not None
        self.transport.sendto(codec.encode(reply), addr)

    def error_received(self, exc: Exception) -> None:
        return


class StatusServer:
    """Owns the status UDP endpoint for one node."""

    def __init__(self, node_id: str, store: NoticeStore) -> None:
        self._node_id = node_id
        self._store = store
        self._transport: Optional[asyncio.DatagramTransport] = None

    async def start(self, host: str, port: int) -> None:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _StatusProtocol(self._node_id, self._store),
            local_addr=(host, port),
        )
        self._transport = transport

    @property
    def local_port(self) -> int:
        if self._transport is None:
            raise RuntimeError("status server not started")
        return self._transport.get_extra_info("sockname")[1]

    def close(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None
