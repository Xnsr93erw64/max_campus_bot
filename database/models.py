from typing import List, Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    FRESHMAN = "первокурсник"
    BACHELOR = "бакалавр"
    MASTER = "магистр"
    PHD = "аспирант"

class TaskStatus(str, Enum):
    PENDING = "ожидает"
    IN_PROGRESS = "в работе"
    COMPLETED = "выполнено"
    OVERDUE = "просрочено"

class User:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.university: Optional[str] = None
        self.group: Optional[str] = None
        self.role: Optional[UserRole] = None
        self.calendar_url: Optional[str] = None
        self.tags: List[str] = []
        self.onboarding_completed: bool = False
        self.created_at = datetime.now()

class Task:
    def __init__(self, user_id: int, title: str, deadline: datetime):
        import uuid
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        self.description: Optional[str] = None
        self.deadline = deadline
        self.subject: str = "другое"
        self.tags: List[str] = []
        self.status: TaskStatus = TaskStatus.PENDING
        self.priority: int = 1
        self.estimated_pomodoros: int = 1
        self.completed_pomodoros: int = 0

class FocusSession:
    def __init__(self, user_id: int, duration: int):
        import uuid
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.task_id: Optional[str] = None
        self.start_time = datetime.now()
        self.duration = duration
        self.completed: bool = False
