from src.estado.notice import Notice
from src.estado.store import NoticeStore
from src.gossip.engine import GossipEngine


class FakeTransport:
    """In-memory transport that records sent messages instead of using UDP."""

    def __init__(self):
        self.sent = []  # list of (host, port, message)

    def send(self, host, port, message):
        self.sent.append((host, port, message))


def _members():
    # host/port per node id; ports are irrelevant for the fake transport.
    return {
        "A": ("127.0.0.1", 5001),
        "B": ("127.0.0.1", 5002),
    }


def _gossip_msg(sender, notices):
    return {
        "type": "GOSSIP",
        "sender": sender,
        "notices": [n.to_dict() for n in notices],
    }


def _reply_msg(sender, notices):
    return {
        "type": "REPLY",
        "sender": sender,
        "notices": [n.to_dict() for n in notices],
    }


def test_handle_gossip_merges_and_sends_reply():
    store = NoticeStore(origem="A")
    store.add_local("mine")  # A:1
    transport = FakeTransport()
    engine = GossipEngine(node_id="A", store=store, transport=transport, members=_members())

    engine.handle_gossip(_gossip_msg("B", [Notice("B", 1, "from b")]))

    # A merged B:1
    assert store.ids() == {"A:1", "B:1"}
    # A replied to B with its full set
    assert len(transport.sent) == 1
    host, port, msg = transport.sent[0]
    assert (host, port) == ("127.0.0.1", 5002)
    assert msg["type"] == "REPLY"
    assert msg["sender"] == "A"
    assert {n["id"] for n in msg["notices"]} == {"A:1", "B:1"}


def test_handle_reply_merges_only():
    store = NoticeStore(origem="A")
    transport = FakeTransport()
    engine = GossipEngine(node_id="A", store=store, transport=transport, members=_members())

    engine.handle_reply(_reply_msg("B", [Notice("B", 1, "x"), Notice("C", 1, "y")]))

    assert store.ids() == {"B:1", "C:1"}
    # REPLY triggers no further send.
    assert transport.sent == []


def test_send_gossip_sends_full_set_to_peer():
    store = NoticeStore(origem="A")
    store.add_local("mine")  # A:1
    transport = FakeTransport()
    engine = GossipEngine(node_id="A", store=store, transport=transport, members=_members())

    engine.send_gossip("B")

    assert len(transport.sent) == 1
    host, port, msg = transport.sent[0]
    assert (host, port) == ("127.0.0.1", 5002)
    assert msg["type"] == "GOSSIP"
    assert msg["sender"] == "A"
    assert {n["id"] for n in msg["notices"]} == {"A:1"}


def test_push_pull_exchange_yields_union_on_both_sides():
    """CA-08: after one GOSSIP -> REPLY, both stores hold the union."""
    store_a = NoticeStore(origem="A")
    store_a.add_local("a1")  # A:1
    store_b = NoticeStore(origem="B")
    store_b.add_local("b1")  # B:1

    t_a = FakeTransport()
    t_b = FakeTransport()
    members = _members()
    engine_a = GossipEngine("A", store_a, t_a, members)
    engine_b = GossipEngine("B", store_b, t_b, members)

    # A initiates: send GOSSIP to B.
    engine_a.send_gossip("B")
    gossip = t_a.sent[-1][2]

    # B receives GOSSIP: merges A's set, emits REPLY.
    engine_b.handle_gossip(gossip)
    reply = t_b.sent[-1][2]

    # A receives REPLY: merges B's set.
    engine_a.handle_reply(reply)

    assert store_a.ids() == {"A:1", "B:1"}
    assert store_b.ids() == {"A:1", "B:1"}
