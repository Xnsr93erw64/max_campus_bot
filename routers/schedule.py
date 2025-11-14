from aiomax import Router
from aiomax.types import Message
from aiomax import buttons
from aiomax.fsm import FSMCursor
from aiomax.filters import has

from database import user_storage
from routers.focus import FocusState
from services.state_guard import ensure_command_allowed
from services.statistics import send_stats_message

schedule_router = Router()

@schedule_router.on_command("schedule")
async def show_schedule(message: Message, cursor: FSMCursor):
    user = user_storage.get_user(message.sender.user_id)
    if not user or not user.onboarding_completed:
        await message.reply("⚠️ Сначала завершите настройку профиля командой /start")
        return

    if not await ensure_command_allowed(
        message,
        cursor,
        allowed_states={FocusState.WORKING},
    ):
        return

    await message.reply(
        "📚 **Ваше расписание**\n\n"
        f"• 🎓 Вуз: {user.university}\n"
        f"• 👥 Группа: {user.group}\n"
        f"• 🏷️ Предметы: {', '.join(user.tags) if user.tags else 'Не указаны'}\n"
        f"• 📅 Календарь: {'Подключен ✅' if user.calendar_url else 'Не подключен ❌'}\n\n"
        "Используйте команды:\n"
        "• /deadlines - показать дедлайны\n"
        "• /focus - начать фокус-сессию\n"
        "• /stats - статистика продуктивности",
        keyboard=buttons.KeyboardBuilder()
        .add(buttons.MessageButton("📅 Мои дедлайны"))
        .row(buttons.MessageButton("🎯 Начать фокус"), buttons.MessageButton("📊 Статистика"))
    )


@schedule_router.on_message(has("📊 Статистика"))
@schedule_router.on_message(has("📊 Мой прогресс"))
async def schedule_stats_button(message: Message, cursor: FSMCursor):
    if not await ensure_command_allowed(
        message,
        cursor,
        allowed_states={FocusState.WORKING},
    ):
        return

    await send_stats_message(message)
