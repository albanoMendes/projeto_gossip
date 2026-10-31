from pathlib import Path

from src.aplicacao.config import Member, load_members, others

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "members.json"


def test_loads_six_members():
    members = load_members(CONFIG_PATH)
    assert len(members) == 6
    assert set(members.keys()) == {"A", "B", "C", "D", "E", "F"}


def test_member_fields():
    members = load_members(CONFIG_PATH)
    a = members["A"]
    assert isinstance(a, Member)
    assert a.id == "A"
    assert a.host
    assert isinstance(a.gossip_port, int)
    assert isinstance(a.status_port, int)


def test_all_ports_distinct():
    members = load_members(CONFIG_PATH)
    ports = []
    for m in members.values():
        ports.append(m.gossip_port)
        ports.append(m.status_port)
    assert len(ports) == len(set(ports)), "gossip and status ports must all be distinct"


def test_others_excludes_self_and_returns_five():
    members = load_members(CONFIG_PATH)
    peers = others(members, "A")
    assert "A" not in peers
    assert len(peers) == 5
    assert set(peers) == {"B", "C", "D", "E", "F"}
