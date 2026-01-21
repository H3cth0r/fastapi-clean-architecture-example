"""
Property-based tests for domain use cases using Hypothesis.

These tests verify business logic across a wide range of inputs
to ensure robustness and catch edge cases.
"""

from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import given, settings

from api.domain.entities import Task
from api.domain.enums import TaskPriority, TaskStatus
from api.domain.exceptions import (
    InvalidTaskStatusTransitionException,
    TaskAccessDeniedException,
    TaskNotFoundException,
)
from api.domain.tests.strategies import (
    active_client_builder,
    client_with_tasks,
    completed_task_builder,
    pending_task_builder,
    tags_list_builder,
    task_builder,
)
from api.domain.usecases import (
    add_tags_to_task,
    create_task,
    delete_task,
    get_task_by_id,
    list_client_tasks,
    remove_tag_from_task,
    update_task,
)

# ============================================================================
# CREATE TASK TESTS
# ============================================================================


@settings(max_examples=10)
@given(client=active_client_builder())
@pytest.mark.asyncio
async def test_create_task_generates_valid_task(client):
    """Property: Creating a task always generates a valid task with pending status."""
    with patch(
        "api.domain.usecases.repo_create_task",
        new_callable=AsyncMock,
    ) as mock_repo:
        task = await create_task(
            client_id=client.client_id,
            title="Test Task",
            description="Test Description",
            priority="high",
            due_date=None,
        )

        # Verify repo was called with task object
        mock_repo.assert_called_once()
        call_args = mock_repo.call_args
        task_arg = call_args.kwargs["task"]  # Get the task keyword argument
        assert task_arg.client_id == client.client_id
        assert task_arg.title == "Test Task"


@settings(max_examples=10)
@given(client=active_client_builder())
@pytest.mark.asyncio
async def test_create_task_sets_pending_status(client):
    """Property: All newly created tasks have pending status."""
    with patch(
        "api.domain.usecases.repo_create_task",
        new_callable=AsyncMock,
    ) as mock_repo:
        task = await create_task(
            client_id=client.client_id,
            title="New Task",
            description=None,
            priority="medium",
            due_date=None,
        )

        assert task.status == TaskStatus.pending
        assert task.client_id == client.client_id
        mock_repo.assert_called_once()


@settings(max_examples=10)
@given(client=active_client_builder(), tags=tags_list_builder(min_size=1))
@pytest.mark.asyncio
async def test_create_task_with_tags_calls_tag_repo(client, tags):
    """Property: Creating a task with tags triggers the tag repository."""
    # We mock both the create_task repo and the add_tags repo
    with patch(
        "api.domain.usecases.repo_create_task", new_callable=AsyncMock
    ) as mock_create, patch(
        "api.domain.usecases.repo_add_tags_to_task", new_callable=AsyncMock
    ) as mock_add_tags:

        await create_task(client_id=client.client_id, title="Task with Tags", tags=tags)

        # Verify repo_add_tags_to_task is hit
        mock_add_tags.assert_called_once_with(
            task_id=ANY, client_id=client.client_id, tag_names=tags
        )


# ============================================================================
# TAGS MANAGEMENT TESTS
# ============================================================================


@settings(max_examples=10)
@given(task=task_builder(), tags=tags_list_builder(min_size=1))
@pytest.mark.asyncio
async def test_add_tags_to_task_success(task, tags):
    """Property: Adding tags to an existing task calls the repository."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id", new_callable=AsyncMock
    ) as mock_get, patch(
        "api.domain.usecases.repo_add_tags_to_task", new_callable=AsyncMock
    ) as mock_tag_repo:

        # Mock finding the task
        mock_get.return_value = task

        await add_tags_to_task(
            task_id=task.task_id, client_id=task.client_id, tags=tags
        )

        # Ensure we verified ownership first
        mock_get.assert_called_once_with(task_id=task.task_id)

        # Ensure we called the add logic
        mock_tag_repo.assert_called_once_with(
            task_id=task.task_id, client_id=task.client_id, tag_names=tags
        )


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_add_tags_enforces_ownership(task):
    """Property: Cannot add tags to someone else's task."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = task
        different_client = uuid4()

        with pytest.raises(TaskAccessDeniedException):
            await add_tags_to_task(
                task_id=task.task_id, client_id=different_client, tags=["urgent"]
            )


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_remove_tag_from_task_success(task):
    """Property: Removing a tag calls the repository."""
    tag_to_remove = "urgent"

    with patch(
        "api.domain.usecases.repo_get_task_by_id", new_callable=AsyncMock
    ) as mock_get, patch(
        "api.domain.usecases.repo_remove_tag_from_task", new_callable=AsyncMock
    ) as mock_remove_repo:

        mock_get.return_value = task

        await remove_tag_from_task(
            task_id=task.task_id, client_id=task.client_id, tag_name=tag_to_remove
        )

        # Ensure ownership check
        mock_get.assert_called_once()

        # Ensure remove logic called
        mock_remove_repo.assert_called_once_with(
            task_id=task.task_id, client_id=task.client_id, tag_name=tag_to_remove
        )


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_remove_tag_enforces_ownership(task):
    """Property: Cannot remove tags from someone else's task."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = task
        different_client = uuid4()

        with pytest.raises(TaskAccessDeniedException):
            await remove_tag_from_task(
                task_id=task.task_id, client_id=different_client, tag_name="urgent"
            )


# ============================================================================
# GET TASK TESTS
# ============================================================================


@settings(max_examples=10)
@given(client_tasks=client_with_tasks(num_tasks=1))
@pytest.mark.asyncio
async def test_get_task_by_id_returns_task_for_owner(client_tasks):
    """Property: Clients can retrieve their own tasks."""
    client, tasks = client_tasks
    task = tasks[0]

    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = task

        result = await get_task_by_id(
            task_id=task.task_id,
            client_id=client.client_id,
        )

        assert result == task
        mock_repo.assert_called_once_with(task_id=task.task_id)


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_get_task_by_id_raises_not_found_when_missing(task):
    """Property: Getting a non-existent task raises TaskNotFoundException."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = None

        with pytest.raises(TaskNotFoundException):
            await get_task_by_id(
                task_id=task.task_id,
                client_id=task.client_id,
            )


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_get_task_by_id_raises_access_denied_for_wrong_owner(task):
    """Property: Clients cannot access tasks owned by other clients."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = task

        different_client_id = uuid4()

        with pytest.raises(TaskAccessDeniedException):
            await get_task_by_id(
                task_id=task.task_id,
                client_id=different_client_id,
            )


# ============================================================================
# LIST TASKS TESTS
# ============================================================================


@settings(max_examples=10)
@given(client_tasks=client_with_tasks(num_tasks=5))
@pytest.mark.asyncio
async def test_list_tasks_returns_only_client_tasks(client_tasks):
    """Property: List tasks returns only tasks belonging to the client."""
    client, tasks = client_tasks

    with patch(
        "api.domain.usecases.repo_list_client_tasks",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = tasks

        result = await list_client_tasks(
            client_id=client.client_id,
            status=None,
            priority=None,
        )

        assert len(result) == len(tasks)
        assert all(t.client_id == client.client_id for t in result)
        mock_repo.assert_called_once()


@settings(max_examples=10)
@given(client=active_client_builder())
@pytest.mark.asyncio
async def test_list_tasks_empty_for_new_client(client):
    """Property: New clients have no tasks."""
    with patch(
        "api.domain.usecases.repo_list_client_tasks",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = []

        result = await list_client_tasks(
            client_id=client.client_id,
            status=None,
            priority=None,
        )

        assert result == []


# ============================================================================
# UPDATE TASK TESTS
# ============================================================================


@settings(max_examples=10)
@given(task=pending_task_builder())
@pytest.mark.asyncio
async def test_update_task_allows_status_change_to_in_progress(task):
    """Property: Pending tasks can transition to in_progress."""
    updated_task = task.model_copy()
    updated_task.status = TaskStatus.in_progress

    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_get.return_value = task
        mock_update.return_value = updated_task

        result = await update_task(
            task_id=task.task_id,
            client_id=task.client_id,
            status=TaskStatus.in_progress,
        )

        assert result.status == TaskStatus.in_progress


@settings(max_examples=10)
@given(task=completed_task_builder())
@pytest.mark.asyncio
async def test_update_task_prevents_reopening_completed_tasks(task):
    """Property: Completed tasks cannot be reopened to pending status."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = task

        with pytest.raises(InvalidTaskStatusTransitionException):
            await update_task(
                task_id=task.task_id,
                client_id=task.client_id,
                status=TaskStatus.pending,
            )


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_update_task_enforces_ownership(task):
    """Property: Only task owners can update their tasks."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = task

        different_client_id = uuid4()

        with pytest.raises(TaskAccessDeniedException):
            await update_task(
                task_id=task.task_id,
                client_id=different_client_id,
                title="New Title",
            )


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_update_task_allows_partial_updates(task):
    """Property: Tasks can be partially updated (any field can be None)."""
    updated_task = task.model_copy()
    updated_task.title = "Updated Title"

    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_get.return_value = task
        mock_update.return_value = updated_task

        # Only update title, all other fields are None
        result = await update_task(
            task_id=task.task_id,
            client_id=task.client_id,
            title="Updated Title",
            description=None,
            status=None,
            priority=None,
            due_date=None,
        )

        # Verify repo was called
        mock_update.assert_called_once()


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_update_task_updates_description(task):
    """Property: Task description can be updated."""
    updated_task = task.model_copy()
    updated_task.description = "New description"

    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_get.return_value = task
        mock_update.return_value = updated_task

        result = await update_task(
            task_id=task.task_id,
            client_id=task.client_id,
            description="New description",
        )

        mock_update.assert_called_once()
        assert result.description == "New description"


@settings(max_examples=10)
@given(task=pending_task_builder())
@pytest.mark.asyncio
async def test_update_task_updates_status(task):
    """Property: Task status can be updated."""
    updated_task = task.model_copy()
    updated_task.status = TaskStatus.in_progress

    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_get.return_value = task
        mock_update.return_value = updated_task

        result = await update_task(
            task_id=task.task_id,
            client_id=task.client_id,
            status=TaskStatus.in_progress,
        )

        mock_update.assert_called_once()
        assert result.status == TaskStatus.in_progress


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_update_task_updates_priority(task):
    """Property: Task priority can be updated."""
    from api.domain.enums import TaskPriority

    updated_task = task.model_copy()
    updated_task.priority = TaskPriority.high

    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_get.return_value = task
        mock_update.return_value = updated_task

        result = await update_task(
            task_id=task.task_id,
            client_id=task.client_id,
            priority=TaskPriority.high,
        )

        mock_update.assert_called_once()
        assert result.priority == TaskPriority.high


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_update_task_updates_due_date(task):
    """Property: Task due_date can be updated."""
    from datetime import UTC, datetime

    new_due_date = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
    updated_task = task.model_copy()
    updated_task.due_date = new_due_date

    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_get.return_value = task
        mock_update.return_value = updated_task

        result = await update_task(
            task_id=task.task_id,
            client_id=task.client_id,
            due_date=new_due_date,
        )

        mock_update.assert_called_once()
        assert result.due_date == new_due_date


# ============================================================================
# DELETE TASK TESTS
# ============================================================================


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_delete_task_removes_task_for_owner(task):
    """Property: Task owners can delete their own tasks."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "api.domain.usecases.repo_delete_task",
        new_callable=AsyncMock,
    ) as mock_delete:
        mock_get.return_value = task

        await delete_task(
            task_id=task.task_id,
            client_id=task.client_id,
        )

        mock_delete.assert_called_once_with(task_id=task.task_id)


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_delete_task_enforces_ownership(task):
    """Property: Only task owners can delete their tasks."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = task

        different_client_id = uuid4()

        with pytest.raises(TaskAccessDeniedException):
            await delete_task(
                task_id=task.task_id,
                client_id=different_client_id,
            )


@settings(max_examples=10)
@given(task=task_builder())
@pytest.mark.asyncio
async def test_delete_task_raises_not_found_when_missing(task):
    """Property: Deleting a non-existent task raises TaskNotFoundException."""
    with patch(
        "api.domain.usecases.repo_get_task_by_id",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = None

        with pytest.raises(TaskNotFoundException):
            await delete_task(
                task_id=task.task_id,
                client_id=task.client_id,
            )


# ============================================================================
# EXPLICIT COVERAGE TESTS (Deterministic)
# ============================================================================


@pytest.mark.asyncio
async def test_update_task_title_coverage():
    """Deterministic test to ensure line 129 (title update) is covered."""
    # 1. Setup a dummy task
    task_id = uuid4()
    client_id = uuid4()
    original_task = Task(
        task_id=task_id,
        client_id=client_id,
        title="Old Title",
        status=TaskStatus.pending,
        priority=TaskPriority.medium,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # 2. Mock the repository calls
    with patch(
        "api.domain.usecases.repo_get_task_by_id", new_callable=AsyncMock
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task", new_callable=AsyncMock
    ) as mock_update:

        mock_get.return_value = original_task

        # 3. Action: Update ONLY title
        await update_task(
            task_id=task_id, client_id=client_id, title="New Covered Title"
        )

        # 4. Verify
        mock_update.assert_called_once()
        # Verify the object passed to update has the new title
        updated_task_arg = mock_update.call_args.kwargs["task"]
        assert updated_task_arg.title == "New Covered Title"


@pytest.mark.asyncio
async def test_update_task_description_coverage():
    """Deterministic test to ensure line 131 (description update) is covered."""
    # 1. Setup a dummy task
    task_id = uuid4()
    client_id = uuid4()
    original_task = Task(
        task_id=task_id,
        client_id=client_id,
        title="Title",
        description="Old Desc",
        status=TaskStatus.pending,
        priority=TaskPriority.medium,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # 2. Mock the repository calls
    with patch(
        "api.domain.usecases.repo_get_task_by_id", new_callable=AsyncMock
    ) as mock_get, patch(
        "api.domain.usecases.repo_update_task", new_callable=AsyncMock
    ) as mock_update:

        mock_get.return_value = original_task

        # 3. Action: Update ONLY description
        await update_task(
            task_id=task_id, client_id=client_id, description="New Covered Desc"
        )

        # 4. Verify
        mock_update.assert_called_once()
        updated_task_arg = mock_update.call_args.kwargs["task"]
        assert updated_task_arg.description == "New Covered Desc"


@pytest.mark.asyncio
async def test_list_client_tasks_with_status_filter_coverage():
    """Deterministic test to ensure status filter logic (Line 129) is covered."""
    client_id = uuid4()

    with patch(
        "api.domain.usecases.repo_list_client_tasks", new_callable=AsyncMock
    ) as mock_repo:
        mock_repo.return_value = []

        # Action: Pass a specific status
        await list_client_tasks(client_id=client_id, status=TaskStatus.pending)

        # Verify the repo was called with the status
        mock_repo.assert_called_once()
        assert mock_repo.call_args.kwargs["status"] == TaskStatus.pending


@pytest.mark.asyncio
async def test_list_client_tasks_with_priority_filter_coverage():
    """Deterministic test to ensure priority filter logic (Line 131) is covered."""
    client_id = uuid4()

    with patch(
        "api.domain.usecases.repo_list_client_tasks", new_callable=AsyncMock
    ) as mock_repo:
        mock_repo.return_value = []

        # Action: Pass a specific priority
        await list_client_tasks(client_id=client_id, priority=TaskPriority.high)

        # Verify the repo was called with the priority
        mock_repo.assert_called_once()
        assert mock_repo.call_args.kwargs["priority"] == TaskPriority.high
