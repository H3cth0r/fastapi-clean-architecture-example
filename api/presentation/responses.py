from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from api.domain.enums import TaskPriority, TaskStatus

# ============================================================================
# ENVELOPE COMPONENTS (from parent API pattern)
# ============================================================================

DataResponse = TypeVar("DataResponse")


class ErrorDetailResponse(BaseModel):
    """Individual error detail for validation errors"""

    message: str
    location: int | str


class ErrorResponse(BaseModel):
    """Error response structure"""

    code: str
    message: str
    errors: list[ErrorDetailResponse] | None = None
    detail: str | None = None


class BaseResponse(BaseModel, Generic[DataResponse]):
    """
    Base envelope response that wraps all API responses.

    All endpoints return this structure with:
    - success: boolean indicating if request succeeded
    - error: error details if failed
    - data: response payload if succeeded
    """

    success: bool
    error: ErrorResponse | None = None
    data: DataResponse | None = None


# ============================================================================
# DOMAIN RESPONSES
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str = "healthy"
    service: str = "clean-architecture-example"


class TaskResponse(BaseModel):
    """Single task response"""

    task_id: UUID
    client_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskWithTagsResponse(BaseModel):
    """SIngle"""


class TaskListResponse(BaseModel):
    """List of tasks response"""

    tasks: list[TaskResponse]
    count: int


class TagListResponse(BaseModel):
    tags: list[dict]
    count: int
