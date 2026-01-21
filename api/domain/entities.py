from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from api.domain.enums import TaskPriority, TaskStatus


class Client(BaseModel):
    """Client entity - API key holder for authentication"""

    client_id: UUID
    name: str
    api_key: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class Task(BaseModel):
    """Task entity - main business object"""

    task_id: UUID
    client_id: UUID
    title: str = Field(..., max_length=200)
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime


class Tag(BaseModel):
    """Tags entity"""

    tag_id: UUID
    client_id: UUID
    title: str = "Tag"
    created_at: datetime


class TaskTag(BaseModel):
    """Represents the link between a Task and a Tag"""

    task_tag_id: UUID
    task_id: UUID
    tag_id: UUID
