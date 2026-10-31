import io

from src.aplicacao.cli import parse_command
from src.estado.store import NoticeStore
from src.monitoramento.logger import EventLogger


def test_parse_post_command():
    cmd, arg = parse_command("post Reunião às 10h")
    assert cmd == "post"
    assert arg == "Reunião às 10h"


def test_parse_post_trims_leading_keyword_only():
    cmd, arg = parse_command("post   spaced text ")
    assert cmd == "post"
    assert arg == "spaced text"


def test_parse_empty_line():
    cmd, arg = parse_command("   ")
    assert cmd is None
    assert arg is None


def test_parse_unknown_command():
    cmd, arg = parse_command("frobnicate x")
    assert cmd == "frobnicate"
    assert arg == "x"


def test_post_creates_notice_and_logs_created():
    """A 'post' handler must add a local notice and log CRIADO (RF-10.1/10.2)."""
    from src.aplicacao.cli import handle_command

    store = NoticeStore(origem="A")
    buf = io.StringIO()
    logger = EventLogger("A", stream=buf)

    handled = handle_command("post hello world", store, logger)

    assert handled is True
    assert store.ids() == {"A:1"}
    assert "[A] CRIADO aviso=A:1" in buf.getvalue()


def test_post_without_text_is_ignored():
    from src.aplicacao.cli import handle_command

    store = NoticeStore(origem="A")
    buf = io.StringIO()
    logger = EventLogger("A", stream=buf)

    handled = handle_command("post    ", store, logger)

    assert handled is False
    assert store.ids() == set()
