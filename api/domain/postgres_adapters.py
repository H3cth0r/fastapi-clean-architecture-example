from api.data.postgres_models import ClientPostgres, TaskPostgres
from api.domain.entities import Client, Task
from api.domain.enums import TaskPriority, TaskStatus


def client_postgres_adapter(model: ClientPostgres | None) -> Client | None:
    """Convert ClientPostgres model to Client entity"""
    if model is None:
        return None

    return Client(
        client_id=model.client_id,
        name=model.name,
        api_key=model.api_key,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def task_postgres_adapter(model: TaskPostgres | None) -> Task | None:
    """Convert TaskPostgres model to Task entity"""
    if model is None:
        return None

    return Task(
        task_id=model.task_id,
        client_id=model.client_id,
        title=model.title,
        description=model.description,
        status=TaskStatus(model.status),
        priority=TaskPriority(model.priority),
        due_date=model.due_date,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
