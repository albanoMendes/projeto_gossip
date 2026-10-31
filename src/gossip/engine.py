# Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
"""Push-pull gossip engine (RF-05).

The engine implements the two-way (anti-entropy) exchange:

    initiator --GOSSIP(full set)--> peer
    peer merges, --REPLY(full set)--> initiator
    initiator merges

After a successful GOSSIP -> REPLY, both sides hold the union of their sets.
The engine is transport-agnostic: it is given any object exposing
``send(host, port, message)`` (a real UdpTransport or an in-memory fake).
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional, Protocol

from src.estado.notice import Notice
from src.estado.store import NoticeStore
from src.gossip.peer_selector import PeerSelector


class Transport(Protocol):
    def send(self, host: str, port: int, message: dict) -> None: ...


# Optional hooks for logging; kept injectable to avoid a hard dependency on the
# monitoring module from the gossip layer.
SentHook = Callable[[str, str, int], None]  # (msg_type, dest_id, n_notices)
NewHook = Callable[[Notice, str], None]  # (notice, received_from)


class GossipEngine:
    """Handles the GOSSIP/REPLY exchange and outbound gossip for one node."""

    def __init__(
        self,
        node_id: str,
        store: NoticeStore,
        transport: Transport,
        members: dict[str, tuple[str, int]],
        selector: Optional[PeerSelector] = None,
        on_sent: Optional[SentHook] = None,
        on_new: Optional[NewHook] = None,
    ) -> None:
        self._node_id = node_id
        self._store = store
        self._transport = transport
        self._members = members
        self._selector = selector
        self._on_sent = on_sent
        self._on_new = on_new
        self._running = False

    def attach_transport(
        self, transport: Transport, members: dict[str, tuple[str, int]]
    ) -> None:
        """Set the transport and membership after construction.

        Useful when transports must be bound to ephemeral ports before the
        membership map (id -> host/port) can be built.
        """
        self._transport = transport
        self._members = members

    def _full_set_payload(self) -> list[dict]:
        return [n.to_dict() for n in self._store.all()]

    def _send(self, msg_type: str, dest_id: str) -> None:
        host, port = self._members[dest_id]
        notices = self._full_set_payload()
        message = {"type": msg_type, "sender": self._node_id, "notices": notices}
        self._transport.send(host, port, message)
        if self._on_sent is not None:
            self._on_sent(msg_type, dest_id, len(notices))

    def _merge_incoming(self, message: dict) -> None:
        incoming = [Notice.from_dict(d) for d in message.get("notices", [])]
        added = self._store.merge(incoming)
        if self._on_new is not None:
            sender = message.get("sender", "?")
            for notice in added:
                self._on_new(notice, sender)

    def send_gossip(self, dest_id: str) -> None:
        """Push: send a GOSSIP carrying the full local set to ``dest_id``."""
        self._send("GOSSIP", dest_id)

    def handle_gossip(self, message: dict) -> None:
        """Passive thread: merge the GOSSIP set, then REPLY with our full set."""
        self._merge_incoming(message)
        sender = message.get("sender")
        if sender is not None and sender in self._members:
            self._send("REPLY", sender)

    def handle_reply(self, message: dict) -> None:
        """Initiator: merge the REPLY set (pull half of the exchange)."""
        self._merge_incoming(message)

    def run_one_cycle(self) -> None:
        """Run a single gossip cycle: select ``fanout`` peers and GOSSIP each.

        With fanout=2 this issues two independent push-pull exchanges per cycle
        (RF-05.2): one GOSSIP per selected peer.
        """
        if self._selector is None:
            raise RuntimeError("a PeerSelector is required to run cycles")
        for peer in self._selector.select():
            self.send_gossip(peer)

    async def run_cycle_loop(self, interval: float) -> None:
        """Run gossip cycles forever at the given interval (anti-entropy).

        The loop keeps going indefinitely (RF-05.6) until :meth:`stop` is
        called. Using a single coroutine with ``await asyncio.sleep`` keeps all
        state mutation on one event loop, avoiding race conditions.
        """
        self._running = True
        while self._running:
            self.run_one_cycle()
            await asyncio.sleep(interval)

    def stop(self) -> None:
        """Signal the cycle loop to stop after the current iteration."""
        self._running = False
