from database import task_storage, focus_storage
from database.models import TaskStatus


async def send_stats_message(message):
    user_id = message.sender.user_id
    tasks = task_storage.get_user_tasks(user_id)
    sessions = focus_storage.get_user_sessions(user_id)

    completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    completed_sessions = len([s for s in sessions if s.completed])
    total_focus_time = sum(s.duration for s in sessions if s.completed)
    active_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])

    await message.reply(
        "📊 **Ваша статистика продуктивности**\n\n"
        f"• ✅ Выполнено задач: {completed_tasks}\n"
        f"• 🎯 Завершено фокус-сессий: {completed_sessions}\n"
        f"• ⏱️ Всего времени в фокусе: {total_focus_time} минут\n"
        f"• 📅 Активных дедлайнов: {active_tasks}\n\n"
        "Продолжайте в том же духе! "
    )
