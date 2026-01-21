from uuid import UUID, uuid4

from api.data.postgres_models import (
    ClientPostgres,
    TagPostgres,
    TaskPostgres,
    TaskTagPostgres,
)
from api.domain.entities import Client, Task
from api.domain.enums import TaskPriority, TaskStatus
from api.domain.postgres_adapters import client_postgres_adapter, task_postgres_adapter
from api.misc.logging import get_logger

# Initialize logger for repositories
logger = get_logger()

# ============================================================================
# CLIENT REPOSITORIES
# ============================================================================


async def repo_get_client_by_api_key(*, api_key: str) -> Client | None:
    """Get active client by API key"""
    logger.debug(
        f"[api.data.postgres_repositories:repo_get_client_by_api_key] Looking up active client by API key"
    )

    model = await ClientPostgres.get_or_none(api_key=api_key, is_active=True)

    if model:
        logger.debug(
            f"[api.data.postgres_repositories:repo_get_client_by_api_key] Found active client {model.client_id}"
        )
    else:
        logger.debug(
            f"[api.data.postgres_repositories:repo_get_client_by_api_key] No active client found for provided API key"
        )

    return client_postgres_adapter(model) if model else None


# ============================================================================
# TASK REPOSITORIES
# ============================================================================


async def repo_create_task(*, task: Task) -> None:
    """Create new task in database"""
    logger.debug(
        f"[api.data.postgres_repositories:repo_create_task] "
        f"Creating task {task.task_id} for client {task.client_id}"
    )

    await TaskPostgres.create(
        task_id=task.task_id,
        client_id=task.client_id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        due_date=task.due_date,
    )

    logger.debug(
        f"[api.data.postgres_repositories:repo_create_task] Task {task.task_id} inserted into database"
    )


async def repo_get_task_by_id(*, task_id: UUID) -> Task | None:
    """Get task by ID"""
    logger.debug(
        f"[api.data.postgres_repositories:repo_get_task_by_id] Fetching task {task_id}"
    )

    model = await TaskPostgres.get_or_none(task_id=task_id)

    if model:
        logger.debug(
            f"[api.data.postgres_repositories:repo_get_task_by_id] Task {task_id} found"
        )
    else:
        logger.debug(
            f"[api.data.postgres_repositories:repo_get_task_by_id] Task {task_id} not found in database"
        )

    return task_postgres_adapter(model) if model else None


async def repo_list_client_tasks(
    *,
    client_id: UUID,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[Task]:
    """List client tasks with optional filtering by status and priority"""
    filters = []
    if status:
        filters.append(f"status={status.value}")
    if priority:
        filters.append(f"priority={priority.value}")

    filter_str = f" with filters: {', '.join(filters)}" if filters else ""
    logger.debug(
        f"[api.data.postgres_repositories:repo_list_client_tasks] "
        f"Querying tasks for client {client_id}{filter_str}"
    )

    query = TaskPostgres.filter(client_id=client_id)

    if status:
        query = query.filter(status=status.value)
    if priority:
        query = query.filter(priority=priority.value)

    models = await query.order_by("-created_at")
    tasks = [t for m in models if (t := task_postgres_adapter(m)) is not None]

    logger.debug(
        f"[api.data.postgres_repositories:repo_list_client_tasks] "
        f"Retrieved {len(tasks)} tasks from database"
    )

    return tasks


async def repo_update_task(*, task: Task) -> None:
    """Update task in database"""
    logger.debug(
        f"[api.data.postgres_repositories:repo_update_task] Updating task {task.task_id}"
    )

    await TaskPostgres.filter(task_id=task.task_id).update(
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        due_date=task.due_date,
        updated_at=task.updated_at,
    )

    logger.debug(
        f"[api.data.postgres_repositories:repo_update_task] Task {task.task_id} updated in database"
    )


async def repo_delete_task(*, task_id: UUID) -> None:
    """Delete task from database (hard delete)"""
    logger.debug(
        f"[api.data.postgres_repositories:repo_delete_task] Deleting task {task_id}"
    )

    await TaskPostgres.filter(task_id=task_id).delete()

    logger.debug(
        f"[api.data.postgres_repositories:repo_delete_task] Task {task_id} deleted from database"
    )


async def repo_add_tags_to_task(
    *, task_id: UUID, client_id: UUID, tag_names: list[str]
) -> None:
    """
    1. Checks if tags exist for client.
    2. Creates missing tags.
    3. Links tags to the task (idempotent).
    """
    if not tag_names:
        return

    logger.debug(
        f"[api.data.postgres_repositories:repo_add_tags_to_task] "
        f"Processing {len(tag_names)} tags for task {task_id}"
    )

    for name in tag_names:
        # 1. Get or create the tag for this client. We ensure tags are unique per client.
        tag, _ = await TagPostgres.get_or_create(
            client_id=client_id, title=name, defaults={"tag_id": uuid4()}
        )

        # 2. Link Tag to Task. get_or_create ensures we don't duplicate the link
        await TaskTagPostgres.get_or_create(
            task_id=task_id, tag_id=tag.tag_id, defaults={"task_tag_id": uuid4()}
        )

    logger.debug(
        f"[api.data.postgres_repositories:repo_add_tags_to_task] Tags processed successfully"
    )


async def repo_remove_tag_from_task(
    *, task_id: UUID, tag_name: str, client_id: UUID
) -> None:
    """
    Unlink a specific tag froma task by name
    """
    logger.debug(
        f"[api.data.postgres_repositories:repo_remove_tag_from_task] "
        f"Removing tag '{tag_name}' from task {task_id}"
    )

    tag = await TagPostgres.get_or_none(client_id=client_id, title=tag_name)

    if tag:
        await TaskTagPostgres.filter(task_id=task_id, tag_id=tag.tag_id).delete()

    logger.debug(
        f"[api.data.postgres_repositories:repo_remove_tag_from_task] Tag removed (if it existed)"
    )
