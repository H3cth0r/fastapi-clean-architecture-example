from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration"""

    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration"""

    low = "low"
    medium = "medium"
    high = "high"
