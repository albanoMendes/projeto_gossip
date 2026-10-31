# Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
"""Asyncio UDP transport for gossip and status messages (RF-04).

A single :class:`UdpTransport` wraps one UDP endpoint (a datagram protocol bound
to a host/port). Sending applies the JSON codec and the optional loss simulator;
receiving decodes datagrams and invokes a callback. Malformed datagrams are
dropped without crashing the process (RF-04.3).
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional

from src.comunicacao import codec
from src.comunicacao.loss import LossSimulator

MessageCallback = Callable[[dict, tuple], None]
DropLogger = Callable[[dict, str, int], None]


class _Protocol(asyncio.DatagramProtocol):
    """Internal datagram protocol that decodes and dispatches messages."""

    def __init__(self, on_message: MessageCallback) -> None:
        self._on_message = on_message
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        message = codec.decode(data)
        if message is None:
            # Malformed datagram: drop silently, stay alive (RF-04.3).
            return
        self._on_message(message, addr)

    def error_received(self, exc: Exception) -> None:
        # Ignore transient ICMP errors (e.g. port unreachable for a dead peer).
        return


class UdpTransport:
    """A UDP endpoint able to send and receive JSON messages."""

    def __init__(
        self,
        node_id: str,
        on_message: MessageCallback,
        loss: LossSimulator | None = None,
        on_drop: DropLogger | None = None,
    ) -> None:
        self._node_id = node_id
        self._on_message = on_message
        self._loss = loss
        self._on_drop = on_drop
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._protocol: Optional[_Protocol] = None

    async def start(self, host: str, port: int) -> None:
        """Bind the endpoint. Use port 0 for an ephemeral port (tests)."""
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: _Protocol(self._on_message),
            local_addr=(host, port),
        )
        self._transport = transport
        self._protocol = protocol  # type: ignore[assignment]

    @property
    def local_port(self) -> int:
        """The actual bound port (useful when started with port 0)."""
        if self._transport is None:
            raise RuntimeError("transport not started")
        return self._transport.get_extra_info("sockname")[1]

    def send(self, host: str, port: int, message: dict) -> None:
        """Send a message, applying simulated loss on the way out (RF-07).

        If the loss simulator decides to drop, the datagram is not sent and the
        drop is reported through ``on_drop`` (so a ``DESCARTE_SIMULADO`` event
        can be logged).
        """
        if self._transport is None:
            raise RuntimeError("transport not started")
        if self._loss is not None and self._loss.should_drop():
            if self._on_drop is not None:
                self._on_drop(message, host, port)
            return
        self._transport.sendto(codec.encode(message), (host, port))

    def close(self) -> None:
        """Close the endpoint."""
        if self._transport is not None:
            self._transport.close()
            self._transport = None
