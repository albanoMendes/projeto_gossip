from src.estado.notice import Notice
from src.estado.store import NoticeStore


def test_add_local_assigns_sequential_counter_per_origin():
    store = NoticeStore(origem="A")
    n1 = store.add_local("first")
    n2 = store.add_local("second")
    assert n1.id == "A:1"
    assert n2.id == "A:2"
    assert n1.origem == "A"


def test_add_local_counter_is_independent_per_origin():
    a = NoticeStore(origem="A")
    b = NoticeStore(origem="B")
    assert a.add_local("x").id == "A:1"
    assert b.add_local("y").id == "B:1"


def test_merge_incorporates_new_notices():
    store = NoticeStore(origem="A")
    incoming = [Notice("B", 1, "hi"), Notice("C", 1, "yo")]
    added = store.merge(incoming)
    assert {n.id for n in added} == {"B:1", "C:1"}
    assert store.ids() == {"B:1", "C:1"}


def test_merge_ignores_duplicates():
    store = NoticeStore(origem="A")
    store.merge([Notice("B", 1, "hi")])
    added = store.merge([Notice("B", 1, "hi")])
    assert added == []
    assert store.ids() == {"B:1"}


def test_merge_is_idempotent():
    store = NoticeStore(origem="A")
    notices = [Notice("B", 1, "hi"), Notice("B", 2, "ho")]
    store.merge(notices)
    store.merge(notices)
    store.merge(notices)
    assert store.ids() == {"B:1", "B:2"}


def test_merge_is_commutative():
    s1 = NoticeStore(origem="A")
    s2 = NoticeStore(origem="A")
    n_b = Notice("B", 1, "hi")
    n_c = Notice("C", 1, "yo")
    s1.merge([n_b, n_c])
    s2.merge([n_c, n_b])
    assert s1.ids() == s2.ids()


def test_all_returns_notice_objects():
    store = NoticeStore(origem="A")
    store.add_local("mine")
    store.merge([Notice("B", 1, "hi")])
    all_notices = store.all()
    assert all(isinstance(n, Notice) for n in all_notices)
    assert {n.id for n in all_notices} == {"A:1", "B:1"}


def test_local_notice_is_eligible_for_ids():
    store = NoticeStore(origem="A")
    store.add_local("mine")
    assert "A:1" in store.ids()
