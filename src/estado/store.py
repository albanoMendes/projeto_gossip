# Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
"""Local notice store with deduplicating, idempotent merge (RF-03).

The store holds the node's known notices as a map ``id -> Notice``. Merging is
set union by id: incorporating a notice is idempotent and commutative, which is
the formal basis for eventual consistency (the merge reduces entropy between
replicas).
"""

from __future__ import annotations

from src.estado.notice import Notice


class NoticeStore:
    """In-memory set of notices keyed by notice id.

    ``origem`` is this node's own id; it is used to stamp locally created
    notices and to drive the per-origin sequential counter (RF-02.2).
    """

    def __init__(self, origem: str) -> None:
        self._origem = origem
        self._notices: dict[str, Notice] = {}
        self._local_counter = 0

    @property
    def origem(self) -> str:
        return self._origem

    def add_local(self, texto: str) -> Notice:
        """Create a new local notice with the next sequential counter.

        The new notice is added to the store immediately, making it eligible for
        the next gossip exchange (RF-10.2).
        """
        self._local_counter += 1
        notice = Notice(origem=self._origem, contador=self._local_counter, texto=texto)
        self._notices[notice.id] = notice
        return notice

    def merge(self, incoming: list[Notice]) -> list[Notice]:
        """Incorporate unknown notices; ignore duplicates.

        Returns the list of notices that were newly added (useful for logging
        ``NOVO`` events).
        """
        added: list[Notice] = []
        for notice in incoming:
            if notice.id not in self._notices:
                self._notices[notice.id] = notice
                added.append(notice)
        return added

    def ids(self) -> set[str]:
        """Return the set of known notice ids."""
        return set(self._notices.keys())

    def all(self) -> list[Notice]:
        """Return all known notices as a list."""
        return list(self._notices.values())
