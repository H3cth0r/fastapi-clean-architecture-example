from tortoise import fields
from tortoise.models import Model


class ClientPostgres(Model):
    """Client database model for API key authentication"""

    client_id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    api_key = fields.CharField(max_length=255, unique=True, index=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "clients"


class TaskPostgres(Model):
    """Task database model"""

    task_id = fields.UUIDField(pk=True)
    client: fields.ForeignKeyRelation["ClientPostgres"] = fields.ForeignKeyField(
        "models.ClientPostgres",
        related_name="tasks",
        to_field="client_id",
        on_delete=fields.CASCADE
    )
    title = fields.CharField(max_length=200)
    description = fields.TextField(null=True)
    status = fields.CharField(max_length=20, default="pending")
    priority = fields.CharField(max_length=10, default="medium")
    due_date = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tasks"
        indexes = [
            ("client_id",),
            ("client_id", "status"),
            ("client_id", "priority"),
        ]


class TagPostgres(Model):
    tag_id = fields.UUIDField(pk=True)
    client: fields.ForeignKeyRelation["ClientPostgres"] = fields.ForeignKeyField(
        "models.ClientPostgres",
        related_name="tags",
        to_field="client_id",
        on_delete=fields.CASCADE
    )
    title = fields.CharField(max_length=20)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tags"
        # This ensures User A can't have two tags named "Urgent",
        # but User A and User B can both have "Urgent".
        unique_together = (("client_id", "title"),)

class TaskTagPostgres(Model):
    task_tag_id = fields.UUIDField(pk=True)
    task: fields.ForeignKeyRelation["TaskPostgres"] = fields.ForeignKeyField(
        "models.TaskPostgres",
        related_name="task_tags",
        on_delete=fields.CASCADE
    )
    tag: fields.ForeignKeyRelation["TagPostgres"] = fields.ForeignKeyField(
        "models.TagPostgres",
        related_name="task_tags",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "task_tags"
        # Ensures a specific tag isn't added to the same task twice
        unique_together = (("task", "tag"),)
