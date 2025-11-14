import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from .models import User, Task, FocusSession, UserRole, TaskStatus

class UserStorage:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.load_data()
    
    def load_data(self):
        if os.path.exists("data/users.json"):
            try:
                with open("data/users.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_id_str, user_data in data.items():
                        user = User(int(user_id_str))
                        # Convert string dates back to datetime
                        if user_data.get('created_at'):
                            user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                        user.__dict__.update(user_data)
                        # Convert role string back to enum
                        if user_data.get('role'):
                            user.role = UserRole(user_data['role'])
                        self.users[int(user_id_str)] = user
            except Exception as e:
                print(f"Error loading users: {e}")
    
    def save_data(self):
        os.makedirs("data", exist_ok=True)
        data = {}
        for user_id, user in self.users.items():
            user_dict = user.__dict__.copy()
            # Convert datetime to string
            if user_dict.get('created_at'):
                user_dict['created_at'] = user_dict['created_at'].isoformat()
            # Convert enum to string
            if user_dict.get('role'):
                user_dict['role'] = user_dict['role'].value
            data[str(user_id)] = user_dict
        
        with open("data/users.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)
    
    def create_user(self, user_id: int) -> User:
        user = User(user_id)
        self.users[user_id] = user
        self.save_data()
        return user
    
    def update_user(self, user: User):
        self.users[user.user_id] = user
        self.save_data()

class TaskStorage:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.user_tasks: Dict[int, List[str]] = {}
        self.load_data()
    
    def load_data(self):
        if os.path.exists("data/tasks.json"):
            try:
                with open("data/tasks.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        task = Task(task_data['user_id'], task_data['title'], 
                                   datetime.fromisoformat(task_data['deadline']))
                        task.__dict__.update(task_data)
                        # Convert string dates
                        task.deadline = datetime.fromisoformat(task_data['deadline'])
                        # Convert status to enum
                        task.status = TaskStatus(task_data['status'])
                        self.tasks[task_id] = task
                        
                        if task.user_id not in self.user_tasks:
                            self.user_tasks[task.user_id] = []
                        self.user_tasks[task.user_id].append(task_id)
            except Exception as e:
                print(f"Error loading tasks: {e}")
    
    def save_data(self):
        os.makedirs("data", exist_ok=True)
        data = {}
        for task_id, task in self.tasks.items():
            task_dict = task.__dict__.copy()
            # Convert datetime to string
            task_dict['deadline'] = task_dict['deadline'].isoformat()
            # Convert enum to string
            task_dict['status'] = task_dict['status'].value
            data[task_id] = task_dict
        
        with open("data/tasks.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def add_task(self, task: Task):
        self.tasks[task.id] = task
        if task.user_id not in self.user_tasks:
            self.user_tasks[task.user_id] = []
        self.user_tasks[task.user_id].append(task.id)
        self.save_data()
    
    def get_user_tasks(self, user_id: int) -> List[Task]:
        task_ids = self.user_tasks.get(user_id, [])
        return [self.tasks[task_id] for task_id in task_ids if task_id in self.tasks]
    
    def get_upcoming_deadlines(self, user_id: int, days: int = 7) -> List[Task]:
        from datetime import timedelta
        user_tasks = self.get_user_tasks(user_id)
        cutoff_date = datetime.now() + timedelta(days=days)
        
        return [task for task in user_tasks 
                if task.deadline <= cutoff_date and task.status == TaskStatus.PENDING]

class FocusStorage:
    def __init__(self):
        self.sessions: Dict[str, FocusSession] = {}
        self.user_sessions: Dict[int, List[str]] = {}
        self.load_data()

    def load_data(self):
        if os.path.exists("data/focus_sessions.json"):
            try:
                with open("data/focus_sessions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.sessions = {}
                    self.user_sessions = {}
                    for session_id, session_data in data.items():
                        raw_user_id = session_data.get('user_id')
                        try:
                            user_id = int(raw_user_id)
                        except (TypeError, ValueError):
                            continue

                        try:
                            duration = int(session_data.get('duration', 0))
                        except (TypeError, ValueError):
                            duration = 0

                        session = FocusSession(user_id, duration)
                        session.__dict__.update(session_data)
                        session.user_id = user_id
                        session.duration = duration
                        if session_data.get('start_time'):
                            session.start_time = datetime.fromisoformat(session_data['start_time'])
                        self.sessions[session_id] = session
                        if session.user_id not in self.user_sessions:
                            self.user_sessions[session.user_id] = []
                        self.user_sessions[session.user_id].append(session_id)
            except Exception as e:
                print(f"Error loading focus sessions: {e}")

    def save_data(self):
        os.makedirs("data", exist_ok=True)
        data = {}
        for session_id, session in self.sessions.items():
            session_dict = session.__dict__.copy()
            if session_dict.get('start_time'):
                session_dict['start_time'] = session.start_time.isoformat()
            data[session_id] = session_dict

        with open("data/focus_sessions.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def add_session(self, session: FocusSession):
        self.sessions[session.id] = session
        if session.user_id not in self.user_sessions:
            self.user_sessions[session.user_id] = []
        self.user_sessions[session.user_id].append(session.id)
        self.save_data()

    def mark_session_completed(self, session_id: str):
        session = self.sessions.get(session_id)
        if session:
            session.completed = True
            self.save_data()

    def get_user_sessions(self, user_id: int) -> List[FocusSession]:
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[session_id] for session_id in session_ids if session_id in self.sessions]
