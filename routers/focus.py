from aiomax import Router
from aiomax.types import Message
from aiomax.fsm import FSMCursor
from aiomax import buttons
from aiomax.filters import has, state as state_filter
import asyncio
from datetime import datetime, timedelta

from database import user_storage, focus_storage
from database.models import FocusSession
from services.state_guard import ensure_command_allowed

focus_router = Router()


class FocusState:
    SELECT_DURATION = "focus_select_duration"
    WORKING = "focus_working"
    BREAK = "focus_break"
    LONG_BREAK = "focus_long_break"


@focus_router.on_command("focus")
async def start_focus(message: Message, cursor: FSMCursor):
    user = user_storage.get_user(message.sender.user_id)
    if not user or not user.onboarding_completed:
        await message.reply("⚠️ Сначала завершите настройку профиля командой /start")
        return

    if not await ensure_command_allowed(message, cursor):
        return

    cursor.change_state(FocusState.SELECT_DURATION)
    await message.reply(
        "🎯 **Фокус-сессия Pomodoro**\n\n"
        "Выберите продолжительность:\n"
        "• 🍅 25 минут (стандартный Pomodoro)\n"
        "• 🔥 50 минут (глубокая работа)\n"
        "• ⚡ 15 минут (быстрая задача)",
        keyboard=buttons.KeyboardBuilder()
        .add(buttons.MessageButton("🍅 25 мин"), buttons.MessageButton("🔥 50 мин"))
        .add(buttons.MessageButton("⚡ 15 мин")),
    )


# Фильтр передаем как позиционный аргумент
@focus_router.on_message(state_filter(FocusState.SELECT_DURATION))
async def handle_focus_duration(message: Message, cursor: FSMCursor):
    duration_text = message.content.strip()
    duration_map = {"🍅 25 мин": 25, "🔥 50 мин": 50, "⚡ 15 мин": 15}

    if duration_text not in duration_map:
        await message.reply("Пожалуйста, выберите вариант из списка кнопок.")
        return

    duration = duration_map[duration_text]
    user_id = message.sender.user_id

    # Создаем сессию фокуса
    session = FocusSession(user_id, duration)
    focus_storage.add_session(session)

    cursor.change_state(FocusState.WORKING)
    cursor.change_data(
        {
            "focus_start": datetime.now().isoformat(),
            "duration": duration,
            "session_id": session.id,
            "pomodoros_completed": 0,
        }
    )

    end_time = datetime.now() + timedelta(minutes=duration)

    await message.reply(
        f"⏰ **Фокус-сессия началась!**\n\n"
        f"Продолжительность: {duration} минут\n"
        f"Время окончания: {end_time.strftime('%H:%M')}\n\n"
        "🚫 Отключите уведомления\n"
        "💧 Поставьте воду рядом\n"
        "📵 Уберите отвлекающие факторы\n\n"
        "**Удачи в работе!** 💪"
    )

    # Запускаем таймер
    asyncio.create_task(
        focus_timer(user_id, duration, session.id, message.bot, cursor.storage)
    )


async def focus_timer(user_id: int, duration: int, session_id: str, bot, fsm_storage):
    await asyncio.sleep(duration * 60)

    # Помечаем сессию как завершенную
    focus_storage.mark_session_completed(session_id)

    # Сбрасываем состояние пользователя после завершения сессии
    fsm_storage.clear(user_id)

    await bot.send_message(
        text=f"✅ **Фокус-сессия завершена!**\n\n"
        f"Отличная работа! {duration} минут продуктивной работы позади.\n\n"
        "Сделайте перерыв:\n"
        "• 🚶 Пройдитесь 5 минут\n"
        "• 💧 Выпейте воды\n"
        "• 🧘 Сделайте разминку",
        user_id=user_id,
        keyboard=buttons.KeyboardBuilder().add(
            buttons.MessageButton("🔄 Новая сессия"),
            buttons.MessageButton("📊 Статистика"),
        ),
    )


@focus_router.on_message(has("🔄 Новая сессия"))
async def restart_focus_from_button(message: Message, cursor: FSMCursor):
    if not await ensure_command_allowed(message, cursor):
        return

    await start_focus(message, cursor)


@focus_router.on_message(has("🎯 Начать фокус"))
async def start_focus_from_button(message: Message, cursor: FSMCursor):
    if not await ensure_command_allowed(message, cursor):
        return

    await start_focus(message, cursor)


@focus_router.on_message(has("🎯 Начать фокус-сессию"))
async def start_focus_session_from_button(message: Message, cursor: FSMCursor):
    if not await ensure_command_allowed(message, cursor):
        return

    await start_focus(message, cursor)


