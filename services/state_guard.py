from typing import Iterable, Optional

from aiomax.fsm import FSMCursor
from aiomax.types import Message


DEFAULT_DENIED_MESSAGE = (
    "⚠️ Пожалуйста, завершите текущий шаг и воспользуйтесь кнопками, "
    "которые я вам предлагаю на экране."
)


def _normalize_allowed(allowed_states: Optional[Iterable[str]]) -> set[str]:
    if not allowed_states:
        return set()
    return {state for state in allowed_states if state is not None}


async def ensure_command_allowed(
    message: Message,
    cursor: FSMCursor,
    *,
    allowed_states: Optional[Iterable[str]] = None,
    denied_message: str = DEFAULT_DENIED_MESSAGE,
) -> bool:
    """Проверяет, нет ли активного сценария, блокирующего действие."""
    current_state = cursor.get_state()
    if current_state is None:
        return True

    allowed = _normalize_allowed(allowed_states)
    if allowed and current_state in allowed:
        return True

    await message.reply(denied_message)
    return False
