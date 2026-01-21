from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from api.domain.entities import Task
from api.domain.enums import TaskPriority, TaskStatus
from api.domain.usecases import update_task

pytestmark = [pytest.mark.asyncio]


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
