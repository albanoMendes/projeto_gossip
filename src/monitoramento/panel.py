# Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
"""Observer panel (RF-12).

The panel queries each node's dedicated status port (read-only) with a short
per-query timeout. A node that does not answer within the timeout is shown as
``(indisponível)`` and the panel moves on without blocking. Coverage is
reported over the active (responding) nodes. The panel never distributes
notices, selects peers, or participates in replication; if it dies, gossip is
unaffected.
"""

from __future__ import annotations

import asyncio
import socket
from typing import Awaitable, Callable, Optional

from src.aplicacao.config import Member
from src.comunicacao import codec

# A query returns the set of known notice ids for a member, or None if the
# member did not respond within the timeout.
QueryFn = Callable[[Member], Awaitable[Optional[set[str]]]]


async def udp_query(member: Member, timeout: float) -> Optional[set[str]]:
    """Query one node's status port over UDP; return its ids or None on timeout."""
    loop = asyncio.get_event_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    try:
        request = codec.encode({"type": "STATUS_REQUEST", "sender": "panel"})
        sock.sendto(request, (member.host, member.status_port))
        data = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=timeout)
        message = codec.decode(data)
        if message is None or message.get("type") != "STATUS_REPLY":
            return None
        return set(message.get("notices", []))
    except (asyncio.TimeoutError, OSError):
        return None
    finally:
        sock.close()


class Panel:
    """Collects status snapshots from all members."""

    def __init__(
        self,
        members: dict[str, Member],
        query: QueryFn | None = None,
        timeout: float = 0.2,
    ) -> None:
        self._members = members
        self._timeout = timeout
        if query is not None:
            self._query = query
        else:
            self._query = lambda m: udp_query(m, self._timeout)

    async def collect(self) -> dict[str, Optional[set[str]]]:
        """Query every member concurrently; return id-set or None per node."""
        ids = list(self._members.keys())
        results = await asyncio.gather(
            *(self._query(self._members[mid]) for mid in ids)
        )
        return dict(zip(ids, results))


def all_known_ids(snapshot: dict[str, Optional[set[str]]]) -> set[str]:
    """Union of every notice id seen across responding nodes."""
    known: set[str] = set()
    for ids in snapshot.values():
        if ids is not None:
            known |= ids
    return known


def render_panel(notice_id: str, snapshot: dict[str, Optional[set[str]]]) -> str:
    """Render a textual table for a single notice across all nodes."""
    lines = [f"Aviso: {notice_id}", "", "  Nó   Conhece?"]
    active = 0
    knowing = 0
    for node_id in sorted(snapshot.keys()):
        ids = snapshot[node_id]
        if ids is None:
            status = "(indisponível)"
        else:
            active += 1
            if notice_id in ids:
                knowing += 1
                status = "SIM"
            else:
                status = "NÃO"
        lines.append(f"  {node_id}    {status}")
    lines.append("")
    lines.append(f"Cobertura observada: {knowing} de {active} nós ativos")
    return "\n".join(lines)
