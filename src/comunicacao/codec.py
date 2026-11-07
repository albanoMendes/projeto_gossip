"""JSON wire-format codec for gossip and status messages (RF-04.2, RF-04.3).

Message shapes:
    GOSSIP / REPLY: {"type": "GOSSIP"|"REPLY", "sender": "A", "notices": [ ... ]}
    STATUS_REQUEST: {"type": "STATUS_REQUEST", "sender": "panel"}
    STATUS_REPLY:   {"type": "STATUS_REPLY", "sender": "A", "notices": [ids...]}

With N=6 and small notices, a full message fits comfortably in a single UDP
datagram (<< 1500 bytes), so there is no application-level fragmentation.
"""

from __future__ import annotations

import json


def encode(message: dict) -> bytes:
    """Serialize a message dict to UTF-8 JSON bytes."""
    return json.dumps(message).encode("utf-8")


def decode(data: bytes) -> dict | None:
    """Deserialize JSON bytes to a dict.

    Returns ``None`` for any malformed, empty, or non-UTF-8 input, so that the
    receiver can drop a bad datagram without crashing (RF-04.3).
    """
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    return value
