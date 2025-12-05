from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.encoders import jsonable_encoder

from api.domain.enums import TaskPriority, TaskStatus
from api.domain.usecases import (
    create_task,
    delete_task,
    get_task_by_id,
    list_client_tasks,
    update_task,
)
from api.misc.logging import get_logger
from api.presentation.depends import ClientDep
from api.presentation.responses import (
    BaseResponse,
    HealthCheckResponse,
    TaskListResponse,
    TaskResponse,
)
from api.presentation.validations import CreateTaskRequest, UpdateTaskRequest

# Initialize logger for API resources
logger = get_logger()

# ============================================================================
# ROUTERS
# ============================================================================

health_router = APIRouter(prefix="/health", tags=["health"])
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


# ============================================================================
# HEALTH CHECK
# ============================================================================


@health_router.get(
    "/",
    summary="Health check",
    description="Check if the API is running",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[HealthCheckResponse],
)
async def health_check():
    """Health check endpoint - no authentication required"""
    response_data = HealthCheckResponse()
    json = jsonable_encoder(response_data)
    return BaseResponse(success=True, data=json)


# ============================================================================
# CREATE TASK
# ============================================================================


@tasks_router.post(
    "/",
    summary="Create new task",
    description="Create a new task for the authenticated client",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponse[TaskResponse],
)
async def create_task_resource(
    *,
    client: ClientDep,
    body: CreateTaskRequest,
):
    """
    Create a new task.

    - **title**: Task title (required, max 200 chars)
    - **description**: Task description (optional)
    - **priority**: Task priority (low, medium, high) - defaults to medium
    - **due_date**: Task due date (optional)

    Task will be created with 'pending' status.
    """
    logger.info(
        f"[api.presentation.resources:create_task_resource] "
        f"POST /tasks - Client {client.client_id} creating task"
    )

    task = await create_task(
        client_id=client.client_id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        due_date=body.due_date,
    )

    response_data = TaskResponse(**task.model_dump())
    json = jsonable_encoder(response_data)
    return BaseResponse(success=True, data=json)


# ============================================================================
# GET TASK
# ============================================================================


@tasks_router.get(
    "/{task_id}",
    summary="Get task by ID",
    description="Retrieve a specific task by its ID",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[TaskResponse],
)
async def get_task_resource(
    *,
    client: ClientDep,
    task_id: UUID,
):
    """
    Get a task by its ID.

    Returns 404 if task doesn't exist.
    Returns 403 if task doesn't belong to authenticated client.
    """
    logger.info(
        f"[api.presentation.resources:get_task_resource] "
        f"GET /tasks/{task_id} - Client {client.client_id}"
    )

    task = await get_task_by_id(
        task_id=task_id,
        client_id=client.client_id,
    )

    response_data = TaskResponse(**task.model_dump())
    json = jsonable_encoder(response_data)
    return BaseResponse(success=True, data=json)


# ============================================================================
# LIST TASKS
# ============================================================================


@tasks_router.get(
    "/",
    summary="List tasks",
    description="List all tasks for the authenticated client with optional filtering",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[TaskListResponse],
)
async def list_tasks_resource(
    *,
    client: ClientDep,
    status_filter: TaskStatus | None = Query(None, alias="status"),
    priority_filter: TaskPriority | None = Query(None, alias="priority"),
):
    """
    List all tasks for the authenticated client.

    Optional query parameters:
    - **status**: Filter by task status (pending, in_progress, completed, cancelled)
    - **priority**: Filter by priority (low, medium, high)

    Results are ordered by creation date (newest first).
    """
    logger.info(
        f"[api.presentation.resources:list_tasks_resource] "
        f"GET /tasks - Client {client.client_id}"
    )

    tasks = await list_client_tasks(
        client_id=client.client_id,
        status=status_filter,
        priority=priority_filter,
    )

    task_responses = [TaskResponse(**t.model_dump()) for t in tasks]
    response_data = TaskListResponse(tasks=task_responses, count=len(task_responses))
    json = jsonable_encoder(response_data)
    return BaseResponse(success=True, data=json)


# ============================================================================
# UPDATE TASK
# ============================================================================


@tasks_router.patch(
    "/{task_id}",
    summary="Update task",
    description="Update a task (partial update - all fields optional)",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[TaskResponse],
)
async def update_task_resource(
    *,
    client: ClientDep,
    task_id: UUID,
    body: UpdateTaskRequest,
):
    """
    Update a task (partial update).

    All fields are optional - only provided fields will be updated:
    - **title**: Update task title
    - **description**: Update task description
    - **status**: Update task status (pending, in_progress, completed, cancelled)
    - **priority**: Update task priority (low, medium, high)
    - **due_date**: Update due date

    Business rules:
    - Cannot reopen completed tasks (transition from completed to pending is forbidden)
    - Task must belong to authenticated client
    """
    logger.info(
        f"[api.presentation.resources:update_task_resource] "
        f"PATCH /tasks/{task_id} - Client {client.client_id}"
    )

    task = await update_task(
        task_id=task_id,
        client_id=client.client_id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        due_date=body.due_date,
    )

    response_data = TaskResponse(**task.model_dump())
    json = jsonable_encoder(response_data)
    return BaseResponse(success=True, data=json)


# ============================================================================
# DELETE TASK
# ============================================================================


@tasks_router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Permanently delete a task",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task_resource(
    *,
    client: ClientDep,
    task_id: UUID,
):
    """
    Delete a task (hard delete - permanent removal).

    Returns 404 if task doesn't exist.
    Returns 403 if task doesn't belong to authenticated client.
    Returns 204 No Content on success (no response body).
    """
    logger.info(
        f"[api.presentation.resources:delete_task_resource] "
        f"DELETE /tasks/{task_id} - Client {client.client_id}"
    )

    await delete_task(
        task_id=task_id,
        client_id=client.client_id,
    )
