from datetime import UTC, datetime
from uuid import UUID, uuid4

from api.data.postgres_repositories import (
    repo_create_task,
    repo_delete_task,
    repo_get_task_by_id,
    repo_list_client_tasks,
    repo_update_task,
)
from api.domain.entities import Task
from api.domain.enums import TaskPriority, TaskStatus
from api.domain.exceptions import (
    InvalidTaskStatusTransitionException,
    TaskAccessDeniedException,
    TaskNotFoundException,
)


async def create_task(
    *,
    client_id: UUID,
    title: str,
    description: str | None = None,
    priority: TaskPriority = TaskPriority.medium,
    due_date: datetime | None = None,
) -> Task:
    """
    Create a new task

    Business Rules:
    - Task starts with pending status
    - Title is required
    - Priority defaults to medium
    """
    now = datetime.now(UTC)

    task = Task(
        task_id=uuid4(),
        client_id=client_id,
        title=title,
        description=description,
        status=TaskStatus.pending,
        priority=priority,
        due_date=due_date,
        created_at=now,
        updated_at=now,
    )

    await repo_create_task(task=task)
    return task


async def get_task_by_id(
    *,
    task_id: UUID,
    client_id: UUID,
) -> Task:
    """
    Get task by ID, verify ownership

    Business Rules:
    - Task must exist
    - Task must belong to requesting client
    """
    task = await repo_get_task_by_id(task_id=task_id)

    if not task:
        raise TaskNotFoundException()

    if task.client_id != client_id:
        raise TaskAccessDeniedException()

    return task


async def list_client_tasks(
    *,
    client_id: UUID,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[Task]:
    """
    List tasks with optional filtering

    Business Rules:
    - Returns only tasks belonging to client
    - Can filter by status and/or priority
    - Ordered by creation date (newest first)
    """
    return await repo_list_client_tasks(
        client_id=client_id,
        status=status,
        priority=priority,
    )


async def update_task(
    *,
    task_id: UUID,
    client_id: UUID,
    title: str | None = None,
    description: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    due_date: datetime | None = None,
) -> Task:
    """
    Update task, verify ownership

    Business Rules:
    - Task must belong to requesting client
    - Cannot reopen completed tasks
    - All fields are optional (partial update)
    """
    task = await get_task_by_id(task_id=task_id, client_id=client_id)

    # Business rule: Can't move from completed to pending
    if status and task.status == TaskStatus.completed and status == TaskStatus.pending:
        raise InvalidTaskStatusTransitionException(
            detail="Cannot reopen completed task"
        )

    # Update fields (only if provided)
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        task.status = status
    if priority is not None:
        task.priority = priority
    if due_date is not None:
        task.due_date = due_date

    task.updated_at = datetime.now(UTC)

    await repo_update_task(task=task)
    return task


async def delete_task(
    *,
    task_id: UUID,
    client_id: UUID,
) -> None:
    """
    Delete task, verify ownership

    Business Rules:
    - Task must belong to requesting client
    - Hard delete (permanent removal)
    """
    # Verify ownership
    await get_task_by_id(task_id=task_id, client_id=client_id)
    await repo_delete_task(task_id=task_id)
