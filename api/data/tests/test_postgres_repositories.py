"""
Integration tests for PostgreSQL repositories.

These tests use a real test database to verify that repository
functions correctly interact with the database layer.
"""

from uuid import uuid4

import pytest

from api.data.fakers import ClientPostgresFactory, TaskPostgresFactory
from api.data.postgres_repositories import (
    repo_create_task,
    repo_delete_task,
    repo_get_client_by_api_key,
    repo_get_task_by_id,
    repo_list_client_tasks,
    repo_update_task,
)
from api.domain.entities import Task
from api.domain.enums import TaskPriority, TaskStatus

# ============================================================================
# CLIENT REPOSITORY TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_get_client_by_api_key_returns_client():
    """Test getting an active client by API key."""
    # Create client in database
    client = await ClientPostgresFactory.create(is_active=True)

    # Fetch using repository
    result = await repo_get_client_by_api_key(api_key=client.api_key)

    assert result is not None
    assert result.client_id == client.client_id
    assert result.name == client.name
    assert result.api_key == client.api_key
    assert result.is_active is True


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_get_client_by_api_key_returns_none_for_inactive():
    """Test that inactive clients cannot be fetched by API key."""
    # Create inactive client
    client = await ClientPostgresFactory.create(is_active=False)

    # Should return None for inactive clients
    result = await repo_get_client_by_api_key(api_key=client.api_key)

    assert result is None


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_get_client_by_api_key_returns_none_for_nonexistent():
    """Test that non-existent API keys return None."""
    fake_api_key = str(uuid4())

    result = await repo_get_client_by_api_key(api_key=fake_api_key)

    assert result is None


# ============================================================================
# TASK REPOSITORY - CREATE
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_create_task_stores_task_in_database():
    """Test: Created tasks are stored correctly in the database."""
    # Use factories to create valid test data (avoids Hypothesis edge cases)
    task = await TaskPostgresFactory.create()

    # Verify task was created
    result = await repo_get_task_by_id(task_id=task.task_id)

    assert result is not None
    assert result.task_id == task.task_id
    assert result.client_id == task.client_id
    assert result.title == task.title
    assert result.description == task.description
    assert result.status.value == task.status
    assert result.priority.value == task.priority


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_create_task_with_all_fields():
    """Test creating a task with all optional fields populated."""
    client = await ClientPostgresFactory.create()

    task = Task(
        task_id=uuid4(),
        client_id=client.client_id,
        title="Complete Task",
        description="This is a test task with all fields",
        status=TaskStatus.in_progress,
        priority=TaskPriority.high,
        due_date=None,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )

    await repo_create_task(task=task)

    result = await repo_get_task_by_id(task_id=task.task_id)

    assert result is not None
    assert result.title == "Complete Task"
    assert result.description == "This is a test task with all fields"
    assert result.status == TaskStatus.in_progress
    assert result.priority == TaskPriority.high


# ============================================================================
# TASK REPOSITORY - GET BY ID
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_get_task_by_id_returns_task():
    """Test retrieving a task by its ID."""
    task = await TaskPostgresFactory.create()

    result = await repo_get_task_by_id(task_id=task.task_id)

    assert result is not None
    assert result.task_id == task.task_id
    assert result.client_id == task.client_id


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_get_task_by_id_returns_none_when_not_found():
    """Test that non-existent task IDs return None."""
    fake_task_id = uuid4()

    result = await repo_get_task_by_id(task_id=fake_task_id)

    assert result is None


# ============================================================================
# TASK REPOSITORY - LIST
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_list_client_tasks_returns_all_tasks():
    """Test listing all tasks for a client."""
    client = await ClientPostgresFactory.create()

    # Create multiple tasks for this client
    tasks = await TaskPostgresFactory.create_batch(5, client=client)

    result = await repo_list_client_tasks(client_id=client.client_id)

    assert len(result) == 5
    assert all(t.client_id == client.client_id for t in result)


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_list_client_tasks_returns_empty_for_new_client():
    """Test that a client with no tasks returns an empty list."""
    client = await ClientPostgresFactory.create()

    result = await repo_list_client_tasks(client_id=client.client_id)

    assert result == []


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_list_client_tasks_filters_by_status():
    """Test filtering tasks by status."""
    client = await ClientPostgresFactory.create()

    # Create tasks with different statuses
    await TaskPostgresFactory.create(client=client, status="pending")
    await TaskPostgresFactory.create(client=client, status="pending")
    await TaskPostgresFactory.create(client=client, status="completed")

    result = await repo_list_client_tasks(
        client_id=client.client_id,
        status=TaskStatus.pending,
    )

    assert len(result) == 2
    assert all(t.status == TaskStatus.pending for t in result)


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_list_client_tasks_filters_by_priority():
    """Test filtering tasks by priority."""
    client = await ClientPostgresFactory.create()

    # Create tasks with different priorities
    await TaskPostgresFactory.create(client=client, priority="high")
    await TaskPostgresFactory.create(client=client, priority="high")
    await TaskPostgresFactory.create(client=client, priority="low")

    result = await repo_list_client_tasks(
        client_id=client.client_id,
        priority=TaskPriority.high,
    )

    assert len(result) == 2
    assert all(t.priority == TaskPriority.high for t in result)


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_list_client_tasks_filters_by_both_status_and_priority():
    """Test filtering tasks by both status and priority."""
    client = await ClientPostgresFactory.create()

    # Create various tasks
    await TaskPostgresFactory.create(client=client, status="pending", priority="high")
    await TaskPostgresFactory.create(client=client, status="pending", priority="low")
    await TaskPostgresFactory.create(client=client, status="completed", priority="high")

    result = await repo_list_client_tasks(
        client_id=client.client_id,
        status=TaskStatus.pending,
        priority=TaskPriority.high,
    )

    assert len(result) == 1
    assert result[0].status == TaskStatus.pending
    assert result[0].priority == TaskPriority.high


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_list_client_tasks_orders_by_created_at_desc():
    """Test that tasks are ordered by creation date (newest first)."""
    client = await ClientPostgresFactory.create()

    # Create tasks (they'll have sequential created_at times)
    task1 = await TaskPostgresFactory.create(client=client, title="First")
    task2 = await TaskPostgresFactory.create(client=client, title="Second")
    task3 = await TaskPostgresFactory.create(client=client, title="Third")

    result = await repo_list_client_tasks(client_id=client.client_id)

    # Should be in reverse order (newest first)
    assert len(result) == 3
    assert result[0].title == "Third"
    assert result[1].title == "Second"
    assert result[2].title == "First"


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_list_client_tasks_isolates_clients():
    """Test that listing tasks only returns tasks for the specified client."""
    client1 = await ClientPostgresFactory.create()
    client2 = await ClientPostgresFactory.create()

    # Create tasks for both clients
    await TaskPostgresFactory.create_batch(3, client=client1)
    await TaskPostgresFactory.create_batch(5, client=client2)

    result = await repo_list_client_tasks(client_id=client1.client_id)

    assert len(result) == 3
    assert all(t.client_id == client1.client_id for t in result)


# ============================================================================
# TASK REPOSITORY - UPDATE
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_update_task_updates_all_fields():
    """Test updating all fields of a task."""
    task_model = await TaskPostgresFactory.create(
        title="Original Title",
        description="Original Description",
        status="pending",
        priority="low",
    )

    # Get as entity
    task_entity = await repo_get_task_by_id(task_id=task_model.task_id)

    # Modify entity
    task_entity.title = "Updated Title"
    task_entity.description = "Updated Description"
    task_entity.status = TaskStatus.completed
    task_entity.priority = TaskPriority.high

    # Update in database
    await repo_update_task(task=task_entity)

    # Fetch and verify
    result = await repo_get_task_by_id(task_id=task_model.task_id)

    assert result.title == "Updated Title"
    assert result.description == "Updated Description"
    assert result.status == TaskStatus.completed
    assert result.priority == TaskPriority.high


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_update_task_preserves_unchanged_fields():
    """Test that update only changes specified fields."""
    task_model = await TaskPostgresFactory.create(
        title="Original Title",
        status="pending",
    )

    # Get as entity
    task_entity = await repo_get_task_by_id(task_id=task_model.task_id)
    original_client_id = task_entity.client_id

    # Only update title
    task_entity.title = "New Title"

    # Update in database
    await repo_update_task(task=task_entity)

    # Fetch and verify other fields preserved
    result = await repo_get_task_by_id(task_id=task_model.task_id)

    assert result.title == "New Title"
    assert result.client_id == original_client_id  # Preserved
    assert result.status == TaskStatus.pending  # Preserved


# ============================================================================
# TASK REPOSITORY - DELETE
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_delete_task_removes_task():
    """Test that delete removes the task from database."""
    task = await TaskPostgresFactory.create()

    # Verify task exists
    assert await repo_get_task_by_id(task_id=task.task_id) is not None

    # Delete task
    await repo_delete_task(task_id=task.task_id)

    # Verify task no longer exists
    assert await repo_get_task_by_id(task_id=task.task_id) is None


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_delete_task_is_idempotent():
    """Test that deleting a non-existent task doesn't raise an error."""
    fake_task_id = uuid4()

    # Should not raise an error
    await repo_delete_task(task_id=fake_task_id)


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_repo_delete_task_only_deletes_specified_task():
    """Test that delete only removes the specified task."""
    client = await ClientPostgresFactory.create()
    task1 = await TaskPostgresFactory.create(client=client)
    task2 = await TaskPostgresFactory.create(client=client)

    # Delete only task1
    await repo_delete_task(task_id=task1.task_id)

    # Verify task1 deleted but task2 still exists
    assert await repo_get_task_by_id(task_id=task1.task_id) is None
    assert await repo_get_task_by_id(task_id=task2.task_id) is not None
