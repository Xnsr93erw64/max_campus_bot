import asyncio
from datetime import datetime, timedelta
import logging

from database import user_storage, task_storage

logger = logging.getLogger("max_focus_campus.reminder")

class ReminderService:
    def __init__(self, bot):
        self.bot = bot
        self.is_running = False
        self.task = None
        self.user_storage = getattr(bot, "user_storage", None)
        self.task_storage = getattr(bot, "task_storage", None)
    
    async def start(self):
        """Запуск сервиса напоминаний"""
        self.is_running = True
        self.task = asyncio.create_task(self._reminder_loop())
        logger.info("Reminder service started")
    
    async def stop(self):
        """Остановка сервиса напоминаний"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Reminder service stopped")
    
    async def _reminder_loop(self):
        """Основной цикл проверки напоминаний"""
        while self.is_running:
            try:
                await self._check_deadlines()
                await asyncio.sleep(60)  # Проверка каждую минуту
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reminder loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_deadlines(self):
        """Проверка приближающихся дедлайнов"""
        try:
            if not self.user_storage or not self.task_storage:
                logger.warning("Storage is not configured for reminder service")
                return

            # Получаем всех пользователей
            for user_id in list(self.user_storage.users.keys()):
                tasks = self.task_storage.get_upcoming_deadlines(user_id, days=1)
                
                for task in tasks:
                    time_left = task.deadline - datetime.now()
                    
                    # Напоминание за 24 часа
                    if timedelta(hours=23) < time_left <= timedelta(hours=24):
                        await self._send_reminder(user_id, task, "24 часа")
                    
                    # Напоминание за 3 часа
                    elif timedelta(hours=2.5) < time_left <= timedelta(hours=3):
                        await self._send_reminder(user_id, task, "3 часа")
                    
                    # Напоминание за 30 минут
                    elif timedelta(minutes=25) < time_left <= timedelta(minutes=30):
                        await self._send_reminder(user_id, task, "30 минут")
            
        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")
    
    async def _send_reminder(self, user_id: int, task, time_left: str):
        """Отправка напоминания пользователю"""
        try:
            await self.bot.bot.send_message(
                text=f"⏰ **Напоминание о дедлайне!**\n\n"
                     f"**Задание:** {task.title}\n"
                     f"**Дедлайн:** {task.deadline.strftime('%d.%m.%Y в %H:%M')}\n"
                     f"**Осталось:** {time_left}\n\n"
                     f"Не забудьте выполнить задание вовремя! 💪",
                user_id=user_id
            )
            logger.info(f"Sent reminder to user {user_id} for task {task.title}")
        except Exception as e:
            logger.error(f"Error sending reminder to user {user_id}: {e}")
