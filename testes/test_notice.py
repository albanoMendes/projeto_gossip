import dataclasses

import pytest

from src.estado.notice import Notice


def test_id_is_origin_colon_counter():
    n = Notice(origem="A", contador=1, texto="hello")
    assert n.id == "A:1"


def test_fields():
    n = Notice(origem="B", contador=3, texto="meeting at 10h")
    assert n.origem == "B"
    assert n.contador == 3
    assert n.texto == "meeting at 10h"
    assert n.id == "B:3"


def test_is_immutable():
    n = Notice(origem="A", contador=1, texto="hello")
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.texto = "changed"  # type: ignore[misc]


def test_equality_by_value():
    a = Notice(origem="A", contador=1, texto="hello")
    b = Notice(origem="A", contador=1, texto="hello")
    assert a == b


def test_to_dict_round_trip():
    n = Notice(origem="A", contador=2, texto="seminar")
    d = n.to_dict()
    assert d == {"id": "A:2", "origem": "A", "contador": 2, "texto": "seminar"}
    assert Notice.from_dict(d) == n


def test_from_dict_ignores_redundant_id():
    # id is derived; from_dict should rebuild from origem/contador/texto.
    n = Notice.from_dict({"id": "ignored", "origem": "C", "contador": 5, "texto": "x"})
    assert n.id == "C:5"
