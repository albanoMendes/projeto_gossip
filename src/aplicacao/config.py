"""Membership configuration loading.

The cluster has a fixed membership of six nodes (A-F), loaded at startup from a
JSON file. Each node is started with its own ``--id`` and uses this membership
to know every peer's address and ports (RF-01).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Member:
    """A single cluster member and its network coordinates.

    ``gossip_port`` carries GOSSIP/REPLY traffic; ``status_port`` carries the
    read-only STATUS_REQUEST/STATUS_REPLY traffic for the observer panel.
    """

    id: str
    host: str
    gossip_port: int
    status_port: int


def load_members(path: str | Path) -> dict[str, Member]:
    """Load the fixed membership from a JSON config file.

    Returns a mapping of node id -> :class:`Member`.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    members: dict[str, Member] = {}
    for entry in data["members"]:
        member = Member(
            id=entry["id"],
            host=entry["host"],
            gossip_port=int(entry["gossip_port"]),
            status_port=int(entry["status_port"]),
        )
        members[member.id] = member
    return members


def others(members: dict[str, Member], self_id: str) -> list[str]:
    """Return the ids of every member except ``self_id``.

    These are the peers eligible for gossip peer selection (RF-06).
    """
    return [mid for mid in members if mid != self_id]
