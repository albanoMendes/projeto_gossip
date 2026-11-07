import random
from collections import Counter

from src.gossip.peer_selector import PeerSelector

OTHERS = ["B", "C", "D", "E", "F"]


def test_selects_two_peers():
    sel = PeerSelector(OTHERS, fanout=2, rng=random.Random(1))
    peers = sel.select()
    assert len(peers) == 2


def test_two_peers_are_distinct():
    sel = PeerSelector(OTHERS, fanout=2, rng=random.Random(99))
    for _ in range(200):
        peers = sel.select()
        assert peers[0] != peers[1]


def test_never_selects_self():
    # self 'A' is simply not part of the others list given to the selector.
    sel = PeerSelector(OTHERS, fanout=2, rng=random.Random(7))
    for _ in range(200):
        for p in sel.select():
            assert p != "A"
            assert p in OTHERS


def test_deterministic_with_seed():
    a = PeerSelector(OTHERS, fanout=2, rng=random.Random(1234))
    b = PeerSelector(OTHERS, fanout=2, rng=random.Random(1234))
    assert [a.select() for _ in range(20)] == [b.select() for _ in range(20)]


def test_distribution_is_roughly_uniform():
    sel = PeerSelector(OTHERS, fanout=2, rng=random.Random(2024))
    counts = Counter()
    for _ in range(10000):
        for p in sel.select():
            counts[p] += 1
    # Each of 5 peers should appear in a comparable share of the 20000 picks.
    assert set(counts.keys()) == set(OTHERS)
    expected = 20000 / 5
    for peer in OTHERS:
        assert 0.8 * expected < counts[peer] < 1.2 * expected
