from src.comunicacao.codec import decode, encode


def test_round_trip_gossip():
    msg = {
        "type": "GOSSIP",
        "sender": "A",
        "notices": [{"id": "A:1", "origem": "A", "contador": 1, "texto": "hi"}],
    }
    assert decode(encode(msg)) == msg


def test_round_trip_reply():
    msg = {"type": "REPLY", "sender": "B", "notices": []}
    assert decode(encode(msg)) == msg


def test_round_trip_status_request():
    msg = {"type": "STATUS_REQUEST", "sender": "panel"}
    assert decode(encode(msg)) == msg


def test_round_trip_status_reply():
    msg = {"type": "STATUS_REPLY", "sender": "A", "notices": ["A:1", "B:1"]}
    assert decode(encode(msg)) == msg


def test_encode_returns_bytes():
    assert isinstance(encode({"type": "REPLY", "sender": "A", "notices": []}), bytes)


def test_decode_malformed_returns_none():
    assert decode(b"not json at all {{{") is None


def test_decode_empty_returns_none():
    assert decode(b"") is None


def test_decode_invalid_utf8_returns_none():
    assert decode(b"\xff\xfe\xfa") is None
