import io

from src.monitoramento.logger import EventLogger


def _logger():
    buf = io.StringIO()
    return EventLogger(node_id="A", stream=buf), buf


def test_log_created():
    logger, buf = _logger()
    logger.created("A:1")
    assert buf.getvalue().strip() == "[A] CRIADO aviso=A:1"


def test_log_sent():
    logger, buf = _logger()
    logger.sent("GOSSIP", "B", 3)
    assert buf.getvalue().strip() == "[A] ENVIADO tipo=GOSSIP destino=B avisos=3"


def test_log_new():
    logger, buf = _logger()
    logger.new("A:1", "B")
    assert buf.getvalue().strip() == "[A] NOVO aviso=A:1 recebido_de=B"


def test_log_dropped():
    logger, buf = _logger()
    logger.dropped("GOSSIP", "C")
    assert buf.getvalue().strip() == "[A] DESCARTE_SIMULADO tipo=GOSSIP destino=C"


def test_multiple_lines_are_newline_separated():
    logger, buf = _logger()
    logger.created("A:1")
    logger.sent("REPLY", "B", 1)
    lines = buf.getvalue().strip().splitlines()
    assert lines == [
        "[A] CRIADO aviso=A:1",
        "[A] ENVIADO tipo=REPLY destino=B avisos=1",
    ]
