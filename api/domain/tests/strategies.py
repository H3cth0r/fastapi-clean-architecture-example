"""
Hypothesis strategies for property-based testing.

This module provides composite strategies for generating test data
that conforms to domain entity constraints and business rules.
"""

from datetime import datetime
from uuid import UUID, uuid4

from hypothesis.strategies import (
    booleans,
    builds,
    composite,
    datetimes,
    from_regex,
    lists,
    none,
    one_of,
    sampled_from,
    text,
    uuids,
)

from api.domain.entities import Client, Task
from api.domain.enums import TaskPriority, TaskStatus

# ============================================================================
# CLIENT STRATEGIES
# ============================================================================


@composite
def client_builder(
    draw, client_id: UUID | None = None, is_active: bool = True
) -> Client:
    """
    Build a Client entity with optional overrides.

    Args:
        client_id: Optional specific client ID to use
        is_active: Whether the client is active (default: True)

    Returns:
        Client entity with generated or overridden values
    """
    client = draw(builds(Client))

    if client_id is not None:
        client.client_id = client_id

    client.is_active = is_active

    # Ensure name is not empty
    client.name = draw(text(min_size=1, max_size=100))

    # Generate realistic API key format
    client.api_key = str(uuid4())

    return client


@composite
def active_client_builder(draw, client_id: UUID | None = None) -> Client:
    """Build an active Client entity."""
    return draw(client_builder(client_id=client_id, is_active=True))


@composite
def inactive_client_builder(draw, client_id: UUID | None = None) -> Client:
    """Build an inactive Client entity."""
    return draw(client_builder(client_id=client_id, is_active=False))


# ============================================================================
# TASK STRATEGIES
# ============================================================================


@composite
def task_builder(
    draw,
    task_id: UUID | None = None,
    client_id: UUID | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> Task:
    """
    Build a Task entity with optional overrides.

    Args:
        task_id: Optional specific task ID to use
        client_id: Optional specific client ID to use
        status: Optional specific task status
        priority: Optional specific task priority

    Returns:
        Task entity with generated or overridden values
    """
    task = draw(builds(Task))

    if task_id is not None:
        task.task_id = task_id

    if client_id is not None:
        task.client_id = client_id

    if status is not None:
        task.status = status
    else:
        task.status = draw(sampled_from(list(TaskStatus)))

    if priority is not None:
        task.priority = priority
    else:
        task.priority = draw(sampled_from(list(TaskPriority)))

    # Ensure title is not empty and within constraints
    task.title = draw(text(min_size=1, max_size=200))

    # Description can be None or a string
    task.description = draw(one_of(none(), text(max_size=1000)))

    # Due date can be None or a future datetime
    # Note: Hypothesis datetimes() requires naive datetimes (no tzinfo)
    task.due_date = draw(
        one_of(
            none(),
            datetimes(
                min_value=datetime(2025, 1, 1),
                max_value=datetime(2030, 12, 31),
            ),
        )
    )

    return task


@composite
def pending_task_builder(
    draw,
    task_id: UUID | None = None,
    client_id: UUID | None = None,
) -> Task:
    """Build a Task with 'pending' status."""
    return draw(
        task_builder(
            task_id=task_id,
            client_id=client_id,
            status=TaskStatus.pending,
        )
    )


@composite
def in_progress_task_builder(
    draw,
    task_id: UUID | None = None,
    client_id: UUID | None = None,
) -> Task:
    """Build a Task with 'in_progress' status."""
    return draw(
        task_builder(
            task_id=task_id,
            client_id=client_id,
            status=TaskStatus.in_progress,
        )
    )


@composite
def completed_task_builder(
    draw,
    task_id: UUID | None = None,
    client_id: UUID | None = None,
) -> Task:
    """Build a Task with 'completed' status."""
    return draw(
        task_builder(
            task_id=task_id,
            client_id=client_id,
            status=TaskStatus.completed,
        )
    )


@composite
def cancelled_task_builder(
    draw,
    task_id: UUID | None = None,
    client_id: UUID | None = None,
) -> Task:
    """Build a Task with 'cancelled' status."""
    return draw(
        task_builder(
            task_id=task_id,
            client_id=client_id,
            status=TaskStatus.cancelled,
        )
    )


@composite
def high_priority_task_builder(
    draw,
    task_id: UUID | None = None,
    client_id: UUID | None = None,
) -> Task:
    """Build a Task with 'high' priority."""
    return draw(
        task_builder(
            task_id=task_id,
            client_id=client_id,
            priority=TaskPriority.high,
        )
    )


# ============================================================================
# COMPOSITE STRATEGIES FOR RELATED ENTITIES
# ============================================================================


@composite
def client_with_tasks(
    draw,
    num_tasks: int = 3,
) -> tuple[Client, list[Task]]:
    """
    Build a Client with multiple related Tasks.

    Args:
        num_tasks: Number of tasks to generate for the client

    Returns:
        Tuple of (Client, list of Tasks)
    """
    client = draw(active_client_builder())

    tasks = []
    for _ in range(num_tasks):
        task = draw(task_builder(client_id=client.client_id))
        tasks.append(task)

    return client, tasks


@composite
def client_with_pending_tasks(
    draw,
    num_tasks: int = 3,
) -> tuple[Client, list[Task]]:
    """Build a Client with multiple pending Tasks."""
    client = draw(active_client_builder())

    tasks = []
    for _ in range(num_tasks):
        task = draw(pending_task_builder(client_id=client.client_id))
        tasks.append(task)

    return client, tasks


@composite
def tags_list_builder(draw, min_size=0, max_size=5):
    """
    Generate a list of tag strings.
    Ex: ["Urgent", "Backend", "Bug"]
    """
    return draw(
        lists(
            text(
                min_size=1,
                max_size=20,
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
            ),
            min_size=min_size,
            max_size=max_size,
            unique=True,  # Tags should be unique within a request
        )
    )
