import pytest

from api.data.fakers import ClientPostgresFactory, TaskPostgresFactory
from api.data.postgres_models import TagPostgres, TaskTagPostgres
from api.data.postgres_repositories import (
    repo_add_tags_to_task,
    repo_remove_tag_from_task,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.use_db]


async def test_add_tags_creates_and_links_tags():
    """
    Scenario: Adding tags ['work', 'urgent'] to a task.
    Expected:
    - 2 entries in 'tags' table.
    - 2 entries in 'task_tags' table.
    """
    # Setup Data
    client = await ClientPostgresFactory.create()
    task = await TaskPostgresFactory.create(client=client)
    tags_to_add = ["work", "urgent"]

    # 2. Action
    await repo_add_tags_to_task(
        task_id=task.task_id, client_id=client.client_id, tag_names=tags_to_add
    )

    # Assertions
    db_tags = await TagPostgres.filter(client_id=client.client_id).all()
    assert len(db_tags) == 2
    assert {t.title for t in db_tags} == {"work", "urgent"}

    # Check Links created
    links = await TaskTagPostgres.filter(task_id=task.task_id).all()
    assert len(links) == 2


async def test_add_tags_is_idempotent():
    """
    Scenario: Adding 'work' tag twice to the same task.
    Expected: It should not crash, and only 1 tag/link should exist.
    """
    client = await ClientPostgresFactory.create()
    task = await TaskPostgresFactory.create(client=client)

    # Add 'work'
    await repo_add_tags_to_task(
        task_id=task.task_id, client_id=client.client_id, tag_names=["work"]
    )

    # Add 'work' again
    await repo_add_tags_to_task(
        task_id=task.task_id, client_id=client.client_id, tag_names=["work"]
    )

    # Assertions
    count_tags = await TagPostgres.filter(
        client_id=client.client_id, title="work"
    ).count()
    count_links = await TaskTagPostgres.filter(task_id=task.task_id).count()

    assert count_tags == 1
    assert count_links == 1


async def test_tags_are_independent_per_user():
    """
    Scenario: User A adds 'Urgent'. User B adds 'Urgent'.
    Expected:
    - 2 distinct Tag rows in database.
    - User A's task is only linked to User A's tag.
    """
    # Setup User A
    client_a = await ClientPostgresFactory.create()
    task_a = await TaskPostgresFactory.create(client=client_a)

    # Setup User B
    client_b = await ClientPostgresFactory.create()
    task_b = await TaskPostgresFactory.create(client=client_b)

    # Both add "Urgent"
    await repo_add_tags_to_task(
        task_id=task_a.task_id, client_id=client_a.client_id, tag_names=["Urgent"]
    )
    await repo_add_tags_to_task(
        task_id=task_b.task_id, client_id=client_b.client_id, tag_names=["Urgent"]
    )

    # Assertions
    all_urgent_tags = await TagPostgres.filter(title="Urgent").all()

    # Should be 2 different rows because unique_together is (client_id, title)
    assert len(all_urgent_tags) == 2

    # Verify User A's task is linked to User A's tag
    tag_a = await TagPostgres.get(client_id=client_a.client_id, title="Urgent")
    is_linked_a = await TaskTagPostgres.filter(
        task_id=task_a.task_id, tag_id=tag_a.tag_id
    ).exists()
    assert is_linked_a is True


async def test_remove_tag_from_task():
    """
    Scenario: Link 'work' tag, then remove it.
    Expected: The link in 'task_tags' is deleted. The Tag definition remains (optional logic).
    """
    client = await ClientPostgresFactory.create()
    task = await TaskPostgresFactory.create(client=client)

    # Setup: Add tag first
    await repo_add_tags_to_task(
        task_id=task.task_id, client_id=client.client_id, tag_names=["work"]
    )

    # Verify it exists
    assert await TaskTagPostgres.filter(task_id=task.task_id).count() == 1

    # Action: Remove it
    await repo_remove_tag_from_task(
        task_id=task.task_id, client_id=client.client_id, tag_name="work"
    )

    # Assertion: Link is gone
    assert await TaskTagPostgres.filter(task_id=task.task_id).count() == 0

    # Assertion: Tag definition still exists (so user doesn't lose 'work' from autocomplete)
    assert await TagPostgres.filter(client_id=client.client_id, title="work").exists()
