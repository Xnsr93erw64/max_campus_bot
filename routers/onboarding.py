from aiomax import Router
from aiomax.types import Message
from aiomax.fsm import FSMCursor
from aiomax import buttons
from aiomax.filters import state as state_filter

from database import user_storage
from database.models import UserRole
from services.state_guard import ensure_command_allowed

onboarding_router = Router()


class OnboardingState:
    START = "onboarding_start"
    UNIVERSITY = "onboarding_university"
    GROUP = "onboarding_group"
    ROLE = "onboarding_role"
    CALENDAR = "onboarding_calendar"
    TAGS = "onboarding_tags"
    COMPLETE = "onboarding_complete"


@onboarding_router.on_command("start")
async def start_command(message: Message, cursor: FSMCursor):
    user_id = message.sender.user_id

    current_state = cursor.get_state()
    if current_state and not str(current_state).startswith("onboarding"):
        if not await ensure_command_allowed(message, cursor):
            return

    user = user_storage.get_user(user_id)
    if user and user.onboarding_completed:
        await message.reply(
            "👋 С возвращением в MAX Focus Campus!\n\n"
            "Что хотите сделать?\n"
            "• 📅 Добавить дедлайн\n"
            "• 🎯 Начать фокус-сессию\n"
            "• 📊 Посмотреть прогресс",
            keyboard=buttons.KeyboardBuilder()
            .add(buttons.MessageButton("📅 Добавить дедлайн"))
            .row(buttons.MessageButton("🎯 Начать фокус-сессию"))
            .add(buttons.MessageButton("📊 Мой прогресс")),
        )
        return

    cursor.change_state(OnboardingState.START)
    if not user:
        user = user_storage.create_user(user_id)

    await message.reply(
        "🎓 Добро пожаловать в **MAX Focus Campus**!\n\n"
        "Я помогу вам организовать учебный процесс:\n"
        "• 📚 Автоматически собирать дедлайны\n"
        "• 🎯 Следить за фокус-сессиями Pomodoro\n"
        "• ⏰ Напоминать о важных событиях\n\n"
        "Давайте настроим ваш профиль! Это займет всего **60 секунд**.\n\n"
        "**Шаг 1 из 5**: В каком вы вузе учитесь?",
        keyboard=buttons.KeyboardBuilder()
        .add(buttons.MessageButton("МГУ"), buttons.MessageButton("МФТИ"))
        .row(buttons.MessageButton("ВШЭ"), buttons.MessageButton("МГТУ"))
        .add(buttons.MessageButton("Другой вуз")),
    )


# Фильтр передаем как позиционный аргумент
@onboarding_router.on_message(state_filter(OnboardingState.START))
async def process_university(message: Message, cursor: FSMCursor):
    university = message.content
    user = user_storage.get_user(message.sender.user_id)
    user.university = university

    cursor.change_state(OnboardingState.GROUP)
    await message.reply(
        "🎯 **Шаг 2 из 5**: Какая у вас группа или курс?\n\n"
        "Например: `Б05-123` или `1 курс магистратуры`"
    )


@onboarding_router.on_message(state_filter(OnboardingState.GROUP))
async def process_group(message: Message, cursor: FSMCursor):
    group = message.content
    user = user_storage.get_user(message.sender.user_id)
    user.group = group

    cursor.change_state(OnboardingState.ROLE)
    await message.reply(
        "👤 **Шаг 3 из 5**: Кто вы?\n\n" "Выберите наиболее подходящий вариант:",
        keyboard=buttons.KeyboardBuilder()
        .add(buttons.MessageButton("🎓 Первокурсник"))
        .row(buttons.MessageButton("💼 Бакалавр"), buttons.MessageButton("🔬 Магистр"))
        .add(buttons.MessageButton("🎯 Аспирант/Исследователь")),
    )


@onboarding_router.on_message(state_filter(OnboardingState.ROLE))
async def process_role(message: Message, cursor: FSMCursor):
    role_text = message.content
    role_mapping = {
        "🎓 Первокурсник": UserRole.FRESHMAN,
        "💼 Бакалавр": UserRole.BACHELOR,
        "🔬 Магистр": UserRole.MASTER,
        "🎯 Аспирант/Исследователь": UserRole.PHD,
    }

    user = user_storage.get_user(message.sender.user_id)
    user.role = role_mapping.get(role_text, UserRole.BACHELOR)

    cursor.change_state(OnboardingState.CALENDAR)
    await message.reply(
        "📅 **Шаг 4 из 5**: Есть ли у вас ссылка на расписание?\n\n"
        "Если да - пришлите ссылку на .ics файл или публичный календарь.\n"
        'Если нет - просто напишите "пропустить"'
    )


@onboarding_router.on_message(state_filter(OnboardingState.CALENDAR))
async def process_calendar(message: Message, cursor: FSMCursor):
    calendar_input = message.content
    user = user_storage.get_user(message.sender.user_id)

    if calendar_input.lower() != "пропустить":
        user.calendar_url = calendar_input

    cursor.change_state(OnboardingState.TAGS)
    await message.reply(
        "🏷️ **Шаг 5 из 5**: Какие предметы у вас сейчас?\n\n"
        "Перечислите через запятую, например:\n"
        "`математика, программирование, физика, английский`"
    )


@onboarding_router.on_message(state_filter(OnboardingState.TAGS))
async def process_tags(message: Message, cursor: FSMCursor):
    tags_text = message.content
    user = user_storage.get_user(message.sender.user_id)
    user.tags = [tag.strip() for tag in tags_text.split(",")]
    user.onboarding_completed = True

    user_storage.update_user(user)
    cursor.clear()

    await message.reply(
        "🎉 **Настройка завершена!**\n\n"
        f"• 🎓 Вуз: {user.university}\n"
        f"• 👥 Группа: {user.group}\n"
        f"• 👤 Роль: {user.role.value}\n"
        f"• 🏷️ Предметы: {', '.join(user.tags)}\n\n"
        "Теперь вы можете:\n"
        "• 📅 Добавлять дедлайны (просто пришлите текст задания)\n"
        "• 🎯 Запускать фокус-сессии командой /focus\n"
        "• 📊 Смотреть прогресс в мини-приложении\n\n"
        "**MAX Focus Campus готов помочь вам в учебе!** 🚀",
        keyboard=buttons.KeyboardBuilder()
        .add(buttons.MessageButton("📅 Добавить задание"))
        .row(
            buttons.MessageButton("🎯 Начать фокус"),
            buttons.MessageButton("📊 Статистика"),
        ),
    )
