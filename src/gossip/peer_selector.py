"""Random peer selection with fanout (RF-06).

Each cycle a node selects ``fanout`` peers (default 2) uniformly at random from
the other five members. The picks are distinct within a cycle and never include
the node itself (self is excluded by construction: it is not in ``others``).
Peers are selected regardless of whether they are alive (there is no failure
detector).
"""

from __future__ import annotations

import random


class PeerSelector:
    """Selects distinct peers uniformly at random for each gossip cycle."""

    def __init__(
        self,
        others: list[str],
        fanout: int = 2,
        rng: random.Random | None = None,
    ) -> None:
        if fanout < 1:
            raise ValueError("fanout must be >= 1")
        if fanout > len(others):
            raise ValueError("fanout cannot exceed the number of available peers")
        self._others = list(others)
        self._fanout = fanout
        self._rng = rng if rng is not None else random.Random()

    @property
    def fanout(self) -> int:
        return self._fanout

    def select(self) -> list[str]:
        """Return ``fanout`` distinct peer ids chosen uniformly at random."""
        return self._rng.sample(self._others, self._fanout)
