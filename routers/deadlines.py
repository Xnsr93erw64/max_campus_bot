from aiomax import Router
from aiomax.types import Message
from aiomax.fsm import FSMCursor
from aiomax import buttons
from aiomax.filters import has
from datetime import datetime

from database import user_storage, task_storage
from database.models import Task, TaskStatus
from routers.focus import FocusState
from services.nlp_parser import extract_deadline_info
from services.state_guard import ensure_command_allowed

deadlines_router = Router()

# Временное хранилище для найденных дедлайнов
temp_deadlines = {}


@deadlines_router.on_message()
async def handle_deadline_message(message: Message, cursor: FSMCursor):
    user = user_storage.get_user(message.sender.user_id)
    if not user or not user.onboarding_completed:
        return

    if cursor.get_state():
        return

    if message.content.startswith("/") or len(message.content) < 10:
        return

    deadline_info = extract_deadline_info(message.content)

    if deadline_info:
        # Сохраняем временно найденный дедлайн
        temp_deadlines[message.sender.user_id] = deadline_info

        await message.reply(
            f"📅 **Найден дедлайн!**\n\n"
            f"• Задание: {deadline_info['title']}\n"
            f"• Предмет: {deadline_info.get('subject', 'Не указан')}\n"
            f"• Дедлайн: {deadline_info['deadline'].strftime('%d.%m.%Y %H:%M')}\n\n"
            "Добавить в систему?",
            keyboard=buttons.KeyboardBuilder()
            .add(buttons.MessageButton("✅ Добавить дедлайн"))
            .add(buttons.MessageButton("✏️ Редактировать"))
            .add(buttons.MessageButton("❌ Отмена")),
        )


# Фильтр передаем как позиционный аргумент
@deadlines_router.on_message(has("✅ Добавить дедлайн"))
async def confirm_deadline(message: Message, cursor: FSMCursor):
    user_id = message.sender.user_id
    deadline_info = temp_deadlines.get(user_id)

    if deadline_info:
        # Создаем задачу
        task = Task(
            user_id=user_id,
            title=deadline_info["title"],
            deadline=deadline_info["deadline"],
        )
        task.subject = deadline_info.get("subject", "другое")

        task_storage.add_task(task)
        del temp_deadlines[user_id]

        await message.reply(
            f"✅ **Дедлайн добавлен!**\n\n"
            f"• Задание: {task.title}\n"
            f"• Дедлайн: {task.deadline.strftime('%d.%m.%Y в %H:%M')}\n"
            f"• Предмет: {task.subject}\n\n"
            "Я напомню вам за 24 часа, 3 часа и 30 минут до дедлайна! 🎯"
        )
    else:
        await message.reply(
            "❌ Не удалось найти информацию о дедлайне. Попробуйте еще раз."
        )


@deadlines_router.on_command("deadlines")
async def show_deadlines(message: Message, cursor: FSMCursor):
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

    tasks = task_storage.get_upcoming_deadlines(message.sender.user_id, days=30)

    if not tasks:
        await message.reply("📭 У вас нет предстоящих дедлайнов на ближайшие 30 дней!")
        return

    response = "📅 **Ваши ближайшие дедлайны:**\n\n"
    for i, task in enumerate(tasks[:10], 1):  # Показываем первые 10
        days_left = (task.deadline - datetime.now()).days
        status_emoji = "🟢" if days_left > 3 else "🟡" if days_left > 1 else "🔴"

        response += f"{status_emoji} **{task.title}**\n"
        response += f"   📍 {task.subject} | ⏰ {task.deadline.strftime('%d.%m.%Y')}\n"
        response += f"   🕐 Осталось: {days_left} дней\n\n"

    if len(tasks) > 10:
        response += f"... и еще {len(tasks) - 10} дедлайнов"

    await message.reply(response)


@deadlines_router.on_message(has("📅 Мои дедлайны"))
async def deadlines_button(message: Message, cursor: FSMCursor):
    if not await ensure_command_allowed(
        message,
        cursor,
        allowed_states={FocusState.WORKING},
    ):
        return

    await show_deadlines(message, cursor)


@deadlines_router.on_message(has("📅 Добавить дедлайн"))
@deadlines_router.on_message(has("📅 Добавить задание"))
async def add_deadline_hint(message: Message, cursor: FSMCursor):
    if cursor.get_state():
        await message.reply(
            "Сначала завершите текущий шаг, затем можно будет добавить новое задание."
        )
        return

    await message.reply(
        "✍️ Пришлите описание задания одним сообщением: предмет, задачу и срок.\n"
        "Я постараюсь распознать дедлайн автоматически."
    )
