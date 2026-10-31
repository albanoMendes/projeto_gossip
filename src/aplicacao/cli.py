"""Non-blocking CLI command handling (RF-10).

Command parsing is kept pure (no I/O) so it is easy to test. The stdin-reading
loop lives in the Node and runs via ``asyncio.to_thread(input)`` so that waiting
for a command never blocks the event loop or the gossip cycles (RF-10.3).
"""

from __future__ import annotations

from src.estado.store import NoticeStore
from src.monitoramento.logger import EventLogger


def parse_command(line: str) -> tuple[str | None, str | None]:
    """Split a raw input line into ``(command, argument)``.

    Returns ``(None, None)`` for a blank line. The argument is everything after
    the first whitespace-delimited token, stripped of surrounding whitespace.
    """
    stripped = line.strip()
    if not stripped:
        return None, None
    parts = stripped.split(None, 1)
    command = parts[0]
    argument = parts[1].strip() if len(parts) > 1 else ""
    return command, argument


def handle_command(line: str, store: NoticeStore, logger: EventLogger) -> bool:
    """Execute a CLI command. Returns True if an action was performed.

    Currently supports ``post <texto>``: creates a local notice immediately,
    making it eligible for the next gossip exchange, and logs CRIADO.
    """
    command, argument = parse_command(line)
    if command == "post":
        if not argument:
            return False
        notice = store.add_local(argument)
        logger.created(notice.id)
        return True
    return False
