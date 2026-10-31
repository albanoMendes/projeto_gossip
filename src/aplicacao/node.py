# Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
"""Node composition: wires every component around one shared store.

A :class:`Node` creates a single :class:`NoticeStore` and injects it into both
the :class:`GossipEngine` and the :class:`StatusServer`, so gossip and the
read-only observer see exactly the same state. Everything runs on one asyncio
event loop (RF-04, RF-05, RF-10, RF-12):

    - a UDP gossip endpoint whose incoming messages are routed to the engine;
    - a periodic gossip cycle coroutine (fanout=2 at the configured interval);
    - a separate, read-only status endpoint;
    - a non-blocking stdin CLI reading ``post <texto>`` commands.
"""

from __future__ import annotations

import asyncio
import random
import sys
from typing import Optional, TextIO

from src.aplicacao import cli
from src.aplicacao.config import Member
from src.comunicacao.loss import LossSimulator
from src.comunicacao.transport import UdpTransport
from src.estado.store import NoticeStore
from src.gossip.engine import GossipEngine
from src.gossip.peer_selector import PeerSelector
from src.monitoramento.logger import EventLogger
from src.monitoramento.status_server import StatusServer


class Node:
    """A single gossip node (process A-F)."""

    def __init__(
        self,
        node_id: str,
        members: dict[str, Member],
        interval: float = 0.3,
        fanout: int = 2,
        loss_probability: float = 0.0,
        rng: random.Random | None = None,
        log_stream: TextIO | None = None,
    ) -> None:
        self._node_id = node_id
        self._members = members
        self._interval = interval
        self._fanout = fanout
        self._rng = rng if rng is not None else random.Random()

        self.store = NoticeStore(origem=node_id)
        self._logger = EventLogger(node_id, stream=log_stream if log_stream else sys.stdout)
        self.peers = [mid for mid in members if mid != node_id]

        self._loss = LossSimulator(loss_probability, rng=self._rng)
        self._transport = UdpTransport(
            node_id=node_id,
            on_message=self._on_message,
            loss=self._loss,
            on_drop=self._on_drop,
        )
        self._status_server = StatusServer(node_id=node_id, store=self.store)
        selector = PeerSelector(self.peers, fanout=fanout, rng=self._rng)
        self._engine = GossipEngine(
            node_id=node_id,
            store=self.store,
            transport=self._transport,
            members={},  # filled in start() once ports are known
            selector=selector,
            on_sent=self._logger.sent,
            on_new=lambda notice, sender: self._logger.new(notice.id, sender),
        )

        self._cycle_task: Optional[asyncio.Task] = None
        self._cli_task: Optional[asyncio.Task] = None
        self._running = False

    # --- network bindings ----------------------------------------------------

    @property
    def gossip_port(self) -> int:
        return self._transport.local_port

    @property
    def status_port(self) -> int:
        return self._status_server.local_port

    async def start(self) -> None:
        """Bind endpoints, resolve the membership map, and start the loops."""
        self_member = self._members[self._node_id]
        await self._transport.start(self_member.host, self_member.gossip_port)
        await self._status_server.start(self_member.host, self_member.status_port)

        # Build id -> (host, gossip_port) for the engine. When the configured
        # port is 0 (ephemeral, used in tests), substitute the actual local
        # port for our own id so self-addressing stays consistent.
        gossip_members: dict[str, tuple[str, int]] = {}
        for mid, m in self._members.items():
            port = self.gossip_port if mid == self._node_id else m.gossip_port
            gossip_members[mid] = (m.host, port)
        self._engine.attach_transport(self._transport, gossip_members)

        self._running = True
        self._cycle_task = asyncio.create_task(self._engine.run_cycle_loop(self._interval))

    def start_cli(self) -> None:
        """Start the non-blocking stdin CLI loop (not used in headless tests)."""
        self._cli_task = asyncio.create_task(self._cli_loop())

    async def _cli_loop(self) -> None:
        loop = asyncio.get_running_loop()
        while self._running:
            try:
                line = await asyncio.to_thread(input)
            except (EOFError, asyncio.CancelledError):
                break
            if not self._running:
                break
            cli.handle_command(line, self.store, self._logger)

    # --- message routing ------------------------------------------------------

    def _on_message(self, message: dict, addr: tuple) -> None:
        msg_type = message.get("type")
        if msg_type == "GOSSIP":
            self._engine.handle_gossip(message)
        elif msg_type == "REPLY":
            self._engine.handle_reply(message)
        # Any other type is ignored (status traffic uses a different port).

    def _on_drop(self, message: dict, host: str, port: int) -> None:
        dest = self._dest_id_for(host, port)
        self._logger.dropped(message.get("type", "?"), dest)

    def _dest_id_for(self, host: str, port: int) -> str:
        for mid, m in self._members.items():
            known_port = self.gossip_port if mid == self._node_id else m.gossip_port
            if m.host == host and known_port == port:
                return mid
        return f"{host}:{port}"

    # --- CLI action (also directly callable in tests) -------------------------

    def post(self, texto: str) -> None:
        """Create a local notice (as the ``post`` CLI command would)."""
        cli.handle_command(f"post {texto}", self.store, self._logger)

    # --- shutdown -------------------------------------------------------------

    async def stop(self) -> None:
        """Stop loops and close endpoints (fail-stop; no persistence)."""
        self._running = False
        self._engine.stop()
        if self._cycle_task is not None:
            self._cycle_task.cancel()
            try:
                await self._cycle_task
            except asyncio.CancelledError:
                pass
        if self._cli_task is not None:
            self._cli_task.cancel()
        self._transport.close()
        self._status_server.close()
