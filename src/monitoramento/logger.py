"""Event logging in the format ``[<id>] EVENTO chave=valor`` (RF-11).

The logger writes to an injectable stream (defaults to stdout), so tests can
capture output and the node can direct logs to the console during the demo.
"""

from __future__ import annotations

import sys
from typing import TextIO


class EventLogger:
    """Emits human-readable, consistent one-line events for one node."""

    def __init__(self, node_id: str, stream: TextIO | None = None) -> None:
        self._node_id = node_id
        self._stream = stream if stream is not None else sys.stdout

    def _emit(self, body: str) -> None:
        self._stream.write(f"[{self._node_id}] {body}\n")
        self._stream.flush()

    def created(self, notice_id: str) -> None:
        """A notice was created locally."""
        self._emit(f"CRIADO aviso={notice_id}")

    def sent(self, msg_type: str, dest_id: str, n_notices: int) -> None:
        """A GOSSIP or REPLY was sent to a peer."""
        self._emit(f"ENVIADO tipo={msg_type} destino={dest_id} avisos={n_notices}")

    def new(self, notice_id: str, received_from: str) -> None:
        """A previously unknown notice was merged into the local store."""
        self._emit(f"NOVO aviso={notice_id} recebido_de={received_from}")

    def dropped(self, msg_type: str, dest_id: str) -> None:
        """An outgoing message was dropped by the loss simulator."""
        self._emit(f"DESCARTE_SIMULADO tipo={msg_type} destino={dest_id}")
