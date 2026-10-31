import asyncio

import pytest

from src.aplicacao.config import Member
from src.monitoramento.panel import Panel, render_panel


def _members():
    return {
        mid: Member(mid, "127.0.0.1", 5000 + i, 6000 + i)
        for i, mid in enumerate("ABCDEF", start=1)
    }


@pytest.mark.asyncio
async def test_collect_marks_unavailable_nodes():
    members = _members()

    async def fake_query(member):
        # Only A, B, D respond; C, E, F time out (return None).
        responses = {
            "A": {"A:1"},
            "B": {"A:1"},
            "D": {"A:1"},
        }
        return responses.get(member.id)

    panel = Panel(members, query=fake_query, timeout=0.2)
    snapshot = await panel.collect()

    assert snapshot["A"] == {"A:1"}
    assert snapshot["B"] == {"A:1"}
    assert snapshot["D"] == {"A:1"}
    assert snapshot["C"] is None  # unavailable
    assert snapshot["E"] is None
    assert snapshot["F"] is None


def test_render_shows_known_unknown_and_unavailable():
    snapshot = {
        "A": {"A:1"},
        "B": {"A:1"},
        "C": set(),
        "D": {"A:1"},
        "E": set(),
        "F": None,  # unavailable
    }
    text = render_panel("A:1", snapshot)
    assert "Aviso: A:1" in text
    assert "A" in text and "SIM" in text
    assert "NÃO" in text
    assert "(indisponível)" in text
    # Coverage counts only active (responding) nodes: 3 of 5 know A:1.
    assert "3 de 5" in text


def test_render_coverage_over_active_nodes_only():
    snapshot = {
        "A": {"A:1"},
        "B": {"A:1"},
        "C": {"A:1"},
        "D": {"A:1"},
        "E": {"A:1"},
        "F": None,  # the stopped node is excluded from the denominator
    }
    text = render_panel("A:1", snapshot)
    assert "5 de 5" in text
