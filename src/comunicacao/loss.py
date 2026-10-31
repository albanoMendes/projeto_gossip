"""Simulated message loss on send (RF-07).

A configurable drop probability is applied to any outgoing message (GOSSIP or
REPLY). There is no ACK or directed retransmission; lost messages are repaired
by subsequent periodic exchanges and by alternative propagation paths.
"""

from __future__ import annotations

import random


class LossSimulator:
    """Decides whether an outgoing message should be dropped.

    The RNG is injectable so tests can be deterministic with a fixed seed.
    """

    def __init__(self, probability: float, rng: random.Random | None = None) -> None:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be in [0.0, 1.0]")
        self._probability = probability
        self._rng = rng if rng is not None else random.Random()

    @property
    def probability(self) -> float:
        return self._probability

    def should_drop(self) -> bool:
        """Return True if this message should be dropped (not delivered)."""
        if self._probability <= 0.0:
            return False
        if self._probability >= 1.0:
            return True
        return self._rng.random() < self._probability
