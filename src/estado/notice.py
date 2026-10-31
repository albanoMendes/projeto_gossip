"""Immutable notice model (RF-02).

A notice is a small, immutable unit of information identified by
``origem:contador`` (e.g. ``A:1``). There is no edit or delete, which keeps the
demo focused on dissemination without conflict resolution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Notice:
    """A single bulletin-board notice.

    ``id`` is derived from ``origem`` and ``contador`` and is used as the
    deduplication key in the local store (RF-03).
    """

    origem: str
    contador: int
    texto: str

    @property
    def id(self) -> str:
        return f"{self.origem}:{self.contador}"

    def to_dict(self) -> dict:
        """Serialize to a plain dict (for JSON wire format)."""
        return {
            "id": self.id,
            "origem": self.origem,
            "contador": self.contador,
            "texto": self.texto,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Notice":
        """Rebuild a notice from a dict.

        The ``id`` field, if present, is ignored: it is always derived from
        ``origem`` and ``contador`` to avoid trusting a redundant wire value.
        """
        return cls(
            origem=data["origem"],
            contador=int(data["contador"]),
            texto=data["texto"],
        )
