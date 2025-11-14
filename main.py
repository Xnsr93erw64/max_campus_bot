from aiomax import Bot, Router
import asyncio
import logging
import signal
import sys

from config import Config
from database import user_storage, task_storage, focus_storage
from routers import (
    onboarding_router,
    deadlines_router,
    focus_router,
    schedule_router,
    FocusState,
)
from services.reminder import ReminderService
from services.state_guard import ensure_command_allowed
from services.statistics import send_stats_message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("max_focus_campus")

class FocusCampusBot:
    def __init__(self):
        self.bot = Bot(
            access_token=Config.BOT_TOKEN,
            command_prefixes=["/", "!"],
            mention_prefix=True,
            case_sensitive=False,
            default_format="markdown",
            max_messages_cached=1000
        )
        
        # Сохраняем ссылки на хранилища в боте для доступа из обработчиков
        self.bot.user_storage = user_storage
        self.bot.task_storage = task_storage
        self.bot.focus_storage = focus_storage

        # Локальные ссылки на хранилища
        self.user_storage = user_storage
        self.task_storage = task_storage
        self.focus_storage = focus_storage
        
        # Сервисы
        self.reminder_service = ReminderService(self)
        self.bot.reminder_service = self.reminder_service
        
        self.setup_routers()
        self.setup_global_handlers()
        
    def setup_routers(self):
        """Регистрация всех роутеров"""
        self.bot.add_router(onboarding_router)
        self.bot.add_router(deadlines_router)
        self.bot.add_router(focus_router)
        self.bot.add_router(schedule_router)
        
    def setup_global_handlers(self):
        """Глобальные обработчики"""
        @self.bot.on_command("help")
        async def help_command(message):
            await message.reply(
                "🆘 **Помощь по MAX Focus Campus**\n\n"
                "Основные команды:\n"
                "• /start - начать работу с ботом\n"
                "• /focus - начать фокус-сессию Pomodoro\n"
                "• /deadlines - показать ближайшие дедлайны\n"
                "• /schedule - информация о вашем расписании\n"
                "• /help - показать эту справку\n\n"
                "Просто пришлите текст задания с датой, и я автоматически его добавлю! 🎯"
            )
        
        @self.bot.on_command("stats")
        async def stats_command(message, cursor):
            if not await ensure_command_allowed(
                message,
                cursor,
                allowed_states={
                    FocusState.WORKING,
                    FocusState.LONG_BREAK,
                    FocusState.BREAK,
                },
            ):
                return

            await send_stats_message(message)
    
    async def start(self):
        """Запуск бота и всех сервисов"""
        logger.info("Запуск MAX Focus Campus...")
        
        # Запуск сервиса напоминаний
        await self.reminder_service.start()
        
        # Запуск бота
        await self.bot.start_polling()
    
    async def stop(self):
        """Корректная остановка бота"""
        await self.reminder_service.stop()
        logger.info("MAX Focus Campus остановлен")

# Обработка сигналов для корректного завершения
async def shutdown(signal, loop, bot):
    logger.info(f"Получен сигнал {signal.name}...")
    await bot.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main():
    bot = FocusCampusBot()
    
    # Настройка обработчиков сигналов
    loop = asyncio.get_running_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(
            sig, 
            lambda s=sig: asyncio.create_task(shutdown(s, loop, bot))
        )
    
    try:
        await bot.start()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
