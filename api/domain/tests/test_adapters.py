"""
Tests for PostgreSQL adapters (model to entity conversion).

These tests verify that database models are correctly converted
to domain entities.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from hypothesis import given, settings

from api.data.postgres_models import ClientPostgres, TaskPostgres
from api.domain.entities import Client, Task
from api.domain.enums import TaskPriority, TaskStatus
from api.domain.postgres_adapters import client_postgres_adapter, task_postgres_adapter

# ============================================================================
# CLIENT ADAPTER TESTS
# ============================================================================


def test_client_postgres_adapter_converts_model_to_entity():
    """Test that ClientPostgres model is correctly converted to Client entity."""
    # Create a model instance
    model = ClientPostgres(
        client_id=uuid4(),
        name="Test Client",
        api_key="test-api-key-123",
        is_active=True,
    )
    # Set timestamps manually since we're not using the DB
    model.created_at = datetime.now(UTC)
    model.updated_at = datetime.now(UTC)

    # Convert to entity
    entity = client_postgres_adapter(model)

    # Verify conversion
    assert isinstance(entity, Client)
    assert entity.client_id == model.client_id
    assert entity.name == model.name
    assert entity.api_key == model.api_key
    assert entity.is_active == model.is_active
    assert entity.created_at == model.created_at
    assert entity.updated_at == model.updated_at


def test_client_postgres_adapter_returns_none_for_none():
    """Test that adapter returns None when given None."""
    result = client_postgres_adapter(None)
    assert result is None


def test_client_postgres_adapter_handles_inactive_client():
    """Test adapter correctly converts inactive clients."""
    model = ClientPostgres(
        client_id=uuid4(),
        name="Inactive Client",
        api_key="inactive-key",
        is_active=False,
    )
    model.created_at = datetime.now(UTC)
    model.updated_at = datetime.now(UTC)

    entity = client_postgres_adapter(model)

    assert entity.is_active is False


# ============================================================================
# TASK ADAPTER TESTS
# ============================================================================


def test_task_postgres_adapter_converts_model_to_entity():
    """Test that TaskPostgres model is correctly converted to Task entity."""
    client_id = uuid4()

    # Create a model instance
    model = TaskPostgres(
        task_id=uuid4(),
        title="Test Task",
        description="Test Description",
        status="pending",
        priority="high",
        due_date=None,
    )
    # Set the foreign key ID directly (Tortoise ORM auto-generates this attribute)
    model.client_id = client_id
    model.created_at = datetime.now(UTC)
    model.updated_at = datetime.now(UTC)

    # Convert to entity
    entity = task_postgres_adapter(model)

    # Verify conversion
    assert isinstance(entity, Task)
    assert entity.task_id == model.task_id
    assert entity.client_id == client_id
    assert entity.title == model.title
    assert entity.description == model.description
    assert entity.status == TaskStatus.pending
    assert entity.priority == TaskPriority.high
    assert entity.due_date is None
    assert entity.created_at == model.created_at
    assert entity.updated_at == model.updated_at


def test_task_postgres_adapter_returns_none_for_none():
    """Test that adapter returns None when given None."""
    result = task_postgres_adapter(None)
    assert result is None


def test_task_postgres_adapter_converts_all_statuses():
    """Test adapter correctly converts all task statuses."""
    statuses = [
        ("pending", TaskStatus.pending),
        ("in_progress", TaskStatus.in_progress),
        ("completed", TaskStatus.completed),
        ("cancelled", TaskStatus.cancelled),
    ]

    for status_str, status_enum in statuses:
        model = TaskPostgres(
            task_id=uuid4(),
            title="Task",
            description=None,
            status=status_str,
            priority="medium",
            due_date=None,
        )
        # Set the foreign key ID directly (Tortoise ORM auto-generates this attribute)
        model.client_id = uuid4()
        model.created_at = datetime.now(UTC)
        model.updated_at = datetime.now(UTC)

        entity = task_postgres_adapter(model)

        assert entity.status == status_enum, f"Failed for status: {status_str}"


def test_task_postgres_adapter_converts_all_priorities():
    """Test adapter correctly converts all task priorities."""
    priorities = [
        ("low", TaskPriority.low),
        ("medium", TaskPriority.medium),
        ("high", TaskPriority.high),
    ]

    for priority_str, priority_enum in priorities:
        model = TaskPostgres(
            task_id=uuid4(),
            title="Task",
            description=None,
            status="pending",
            priority=priority_str,
            due_date=None,
        )
        # Set the foreign key ID directly (Tortoise ORM auto-generates this attribute)
        model.client_id = uuid4()
        model.created_at = datetime.now(UTC)
        model.updated_at = datetime.now(UTC)

        entity = task_postgres_adapter(model)

        assert entity.priority == priority_enum, f"Failed for priority: {priority_str}"


def test_task_postgres_adapter_handles_null_description():
    """Test adapter handles tasks with null description."""
    model = TaskPostgres(
        task_id=uuid4(),
        title="Task without description",
        description=None,
        status="pending",
        priority="medium",
        due_date=None,
    )
    # Set the foreign key ID directly (Tortoise ORM auto-generates this attribute)
    model.client_id = uuid4()
    model.created_at = datetime.now(UTC)
    model.updated_at = datetime.now(UTC)

    entity = task_postgres_adapter(model)

    assert entity.description is None


def test_task_postgres_adapter_handles_due_date():
    """Test adapter correctly handles tasks with due dates."""
    due_date = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)

    model = TaskPostgres(
        task_id=uuid4(),
        title="Task with due date",
        description="Important task",
        status="pending",
        priority="high",
        due_date=due_date,
    )
    # Set the foreign key ID directly (Tortoise ORM auto-generates this attribute)
    model.client_id = uuid4()
    model.created_at = datetime.now(UTC)
    model.updated_at = datetime.now(UTC)

    entity = task_postgres_adapter(model)

    assert entity.due_date == due_date


# ============================================================================
# INTEGRATION TESTS WITH DATABASE
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.use_db
async def test_adapter_roundtrip_through_database():
    """
    Integration test: Create model in DB, fetch it, convert to entity.

    This verifies that the adapter works correctly with real database models
    that have been saved and retrieved.
    """
    from api.data.fakers import ClientPostgresFactory, TaskPostgresFactory

    # Create client in database
    client_model = await ClientPostgresFactory.create(
        name="Integration Test Client",
        is_active=True,
    )

    # Create task in database
    task_model = await TaskPostgresFactory.create(
        client=client_model,
        title="Integration Test Task",
        status="pending",
        priority="high",
    )

    # Fetch from database
    from api.data.postgres_models import ClientPostgres, TaskPostgres

    fetched_client = await ClientPostgres.get(client_id=client_model.client_id)
    fetched_task = await TaskPostgres.get(task_id=task_model.task_id)

    # Convert to entities using adapters
    client_entity = client_postgres_adapter(fetched_client)
    task_entity = task_postgres_adapter(fetched_task)

    # Verify entities match original models
    assert client_entity.client_id == client_model.client_id
    assert client_entity.name == "Integration Test Client"

    assert task_entity.task_id == task_model.task_id
    assert task_entity.title == "Integration Test Task"
    assert task_entity.client_id == client_model.client_id
    assert task_entity.status == TaskStatus.pending
    assert task_entity.priority == TaskPriority.high
