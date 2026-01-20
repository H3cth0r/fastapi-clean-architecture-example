from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "clients" (
    "client_id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "api_key" VARCHAR(255) NOT NULL UNIQUE,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_clients_api_key_b5f898" ON "clients" ("api_key");
COMMENT ON TABLE "clients" IS 'Client database model for API key authentication';
CREATE TABLE IF NOT EXISTS "tags" (
    "tag_id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(20) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "client_id" UUID NOT NULL REFERENCES "clients" ("client_id") ON DELETE CASCADE,
    CONSTRAINT "uid_tags_client__030ccc" UNIQUE ("client_id", "title")
);
CREATE TABLE IF NOT EXISTS "tasks" (
    "task_id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'pending',
    "priority" VARCHAR(10) NOT NULL  DEFAULT 'medium',
    "due_date" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "client_id" UUID NOT NULL REFERENCES "clients" ("client_id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_tasks_client__9d5af4" ON "tasks" ("client_id");
CREATE INDEX IF NOT EXISTS "idx_tasks_client__354c3f" ON "tasks" ("client_id", "status");
CREATE INDEX IF NOT EXISTS "idx_tasks_client__e0ec42" ON "tasks" ("client_id", "priority");
COMMENT ON TABLE "tasks" IS 'Task database model';
CREATE TABLE IF NOT EXISTS "task_tags" (
    "task_tag_id" UUID NOT NULL  PRIMARY KEY,
    "tag_id" UUID NOT NULL REFERENCES "tags" ("tag_id") ON DELETE CASCADE,
    "task_id" UUID NOT NULL REFERENCES "tasks" ("task_id") ON DELETE CASCADE,
    CONSTRAINT "uid_task_tags_task_id_4e2287" UNIQUE ("task_id", "tag_id")
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
