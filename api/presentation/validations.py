from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from api.domain.enums import TaskPriority, TaskStatus


class CreateTaskRequest(BaseModel):
    """Request body for creating a new task"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.medium
    due_date: datetime | None = None
    tags: List[str] = []


class UpdateTaskRequest(BaseModel):
    """Request body for updating a task (all fields optional)"""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None


class AddTagsRequest(BaseModel):
    tags: List[str]
