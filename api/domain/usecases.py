from datetime import UTC, datetime
from uuid import UUID, uuid4

from api.data.postgres_repositories import (
    repo_add_tags_to_task,
    repo_create_task,
    repo_delete_task,
    repo_get_tags_by_task_id,
    repo_get_task_by_id,
    repo_list_client_tasks,
    repo_remove_tag_from_task,
    repo_update_task,
)
from api.domain.entities import Tag, Task
from api.domain.enums import TaskPriority, TaskStatus
from api.domain.exceptions import (
    InvalidTaskStatusTransitionException,
    TaskAccessDeniedException,
    TaskNotFoundException,
)
from api.misc.logging import get_logger

# Initialize logger for use cases
logger = get_logger()


async def create_task(
    *,
    client_id: UUID,
    title: str,
    description: str | None = None,
    priority: TaskPriority = TaskPriority.medium,
    due_date: datetime | None = None,
    tags: list[str] = [],
) -> Task:
    """
    Create a new task

    Business Rules:
    - Task starts with pending status
    - Title is required
    - Priority defaults to medium
    """
    logger.info(
        f"[api.domain.usecases:create_task] Creating task '{title}' "
        f"for client {client_id} with priority {priority if isinstance(priority, str) else priority.value}"
    )

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

    if tags:
        await repo_add_tags_to_task(
            task_id=task.task_id, client_id=client_id, tag_names=tags
        )

    logger.info(
        f"[api.domain.usecases:create_task] Task {task.task_id} created successfully "
        f"with status {task.status.value}"
    )

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
    logger.info(
        f"[api.domain.usecases:get_task_by_id] Retrieving task {task_id} for client {client_id}"
    )

    task = await repo_get_task_by_id(task_id=task_id)

    if not task:
        logger.error(f"[api.domain.usecases:get_task_by_id] Task {task_id} not found")
        raise TaskNotFoundException()

    if task.client_id != client_id:
        logger.warning(
            f"[api.domain.usecases:get_task_by_id] Access denied: "
            f"task {task_id} belongs to client {task.client_id}, requested by {client_id}"
        )
        raise TaskAccessDeniedException()

    logger.info(
        f"[api.domain.usecases:get_task_by_id] Task {task_id} retrieved successfully"
    )

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
    filters = []
    if status:
        filters.append(f"status={status.value}")
    if priority:
        filters.append(f"priority={priority.value}")

    filter_str = f" with filters: {', '.join(filters)}" if filters else ""
    logger.info(
        f"[api.domain.usecases:list_client_tasks] Listing tasks for client {client_id}{filter_str}"
    )

    tasks = await repo_list_client_tasks(
        client_id=client_id,
        status=status,
        priority=priority,
    )

    logger.info(
        f"[api.domain.usecases:list_client_tasks] Retrieved {len(tasks)} tasks for client {client_id}"
    )

    return tasks


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
    logger.info(
        f"[api.domain.usecases:update_task] Updating task {task_id} for client {client_id}"
    )

    task = await get_task_by_id(task_id=task_id, client_id=client_id)

    # Business rule: Can't move from completed to pending
    if status and task.status == TaskStatus.completed and status == TaskStatus.pending:
        logger.warning(
            f"[api.domain.usecases:update_task] Cannot reopen completed task {task_id}"
        )
        raise InvalidTaskStatusTransitionException(
            detail="Cannot reopen completed task"
        )

    # Track what's being updated for logging
    updates = []
    if title is not None:
        task.title = title
        updates.append("title")
    if description is not None:
        task.description = description
        updates.append("description")
    if status is not None:
        updates.append(f"status={status.value}")
        task.status = status
    if priority is not None:
        updates.append(f"priority={priority.value}")
        task.priority = priority
    if due_date is not None:
        task.due_date = due_date
        updates.append("due_date")

    task.updated_at = datetime.now(UTC)

    await repo_update_task(task=task)

    logger.info(
        f"[api.domain.usecases:update_task] Task {task_id} updated successfully. "
        f"Fields changed: {', '.join(updates) if updates else 'none'}"
    )

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
    logger.info(
        f"[api.domain.usecases:delete_task] Deleting task {task_id} for client {client_id}"
    )

    # Verify ownership
    await get_task_by_id(task_id=task_id, client_id=client_id)
    await repo_delete_task(task_id=task_id)

    logger.info(
        f"[api.domain.usecases:delete_task] Task {task_id} deleted successfully"
    )


async def add_tags_to_task(*, task_id: UUID, client_id: UUID, tags: list[str]) -> None:
    """Add tags to an existing task"""
    # 1. Verify ownership (Task must exist and belong to client)
    await get_task_by_id(task_id=task_id, client_id=client_id)

    # 2. Add Tags
    await repo_add_tags_to_task(task_id=task_id, client_id=client_id, tag_names=tags)

    logger.info(f"[usecases:add_tags_to_task] Added {len(tags)} tags to task {task_id}")


async def remove_tag_from_task(
    *, task_id: UUID, client_id: UUID, tag_name: str
) -> None:
    # 1. Verify ownership
    await get_task_by_id(task_id=task_id, client_id=client_id)

    # 2. Remove tag
    await repo_remove_tag_from_task(
        task_id=task_id, client_id=client_id, tag_name=tag_name
    )

    logger.info(
        f"[usecases:remove_tag_from_task] Removed tag '{tag_name}' from task {task_id}"
    )


async def get_tags_by_task_id(*, task_id: UUID, client_id: UUID) -> list[Tag]:
    """Get all tags for a task"""
    logger.info(
        f"[api.domain.usecases:get_tags_by_task_id] "
        f"Getting tags for task {task_id}, client {client_id}"
    )

    # Verify ownership
    await get_task_by_id(task_id=task_id, client_id=client_id)

    # Get tags
    tags = await repo_get_tags_by_task_id(task_id=task_id)

    logger.info(
        f"[api.domain.usecases:get_tags_by_task_id] "
        f"Retrieved {len(tags)} tags for task {task_id}"
    )

    return tags
