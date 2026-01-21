from uuid import uuid4

import factory
from async_factory_boy.factory.tortoise import AsyncTortoiseFactory

from api.data.postgres_models import ClientPostgres, TagPostgres, TaskPostgres
from api.domain.enums import TaskPriority, TaskStatus

# ============================================================================
# TORTOISE MODEL FACTORIES (AsyncTortoiseFactory for database tests)
# ============================================================================


class ClientPostgresFactory(AsyncTortoiseFactory):
    """
    Async factory for ClientPostgres models (Tortoise ORM).

    Usage in async tests:
        client = await ClientPostgresFactory.create()
        clients = await ClientPostgresFactory.create_batch(5)
    """

    class Meta:
        model = ClientPostgres

    client_id = factory.Faker("uuid4")
    name = factory.Faker("company")
    api_key = factory.LazyFunction(lambda: str(uuid4()))
    is_active = True


class TaskPostgresFactory(AsyncTortoiseFactory):
    """
    Async factory for TaskPostgres models (Tortoise ORM).

    Usage in async tests:
        task = await TaskPostgresFactory.create()
        task = await TaskPostgresFactory.create(status="completed")
        tasks = await TaskPostgresFactory.create_batch(10)

    With SubFactory for relationships:
        task = await TaskPostgresFactory.create(client=client_instance)
    """

    class Meta:
        model = TaskPostgres

    task_id = factory.Faker("uuid4")
    # Use SubFactory to automatically create related client
    client = factory.SubFactory(ClientPostgresFactory)
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    status = factory.Faker(
        "random_element",
        elements=[status.value for status in TaskStatus],
    )
    priority = factory.Faker(
        "random_element",
        elements=[priority.value for priority in TaskPriority],
    )
    due_date = None


class TagPostgresFactory(AsyncTortoiseFactory):
    """
    Async factory for TagPostgres models.
    """

    class Meta:
        model = TagPostgres

    tag_id = factory.Faker("uuid4")
    # SubFactory ensures a tag is always created with a client parent
    client = factory.SubFactory(ClientPostgresFactory)
    title = factory.Faker("word")
