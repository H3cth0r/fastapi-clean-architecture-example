class BaseException(Exception):
    """Base domain exception with serialization support"""

    code = "error"
    message = ""
    detail = ""

    def __init__(self, code=None, message=None, detail=None) -> None:
        super().__init__(code, message, detail)
        if isinstance(detail, str) and detail:
            self.detail = detail

    def serialize(self) -> dict[str, str]:
        """Serializes exception into a dictionary for JSON responses"""
        data = {"code": self.code, "message": self.message}
        if self.detail:
            data["detail"] = self.detail
        return data


class BusinessException(BaseException):
    """Base class for business logic exceptions (400 Bad Request)"""

    code = "business_error"
    message = "Business error"


class UnauthorizedException(BaseException):
    """Unauthorized access exception (401 Unauthorized)"""

    code = "unauthorized_error"
    message = "Unauthorized"


class NotFoundException(BaseException):
    """Resource not found exception (404 Not Found)"""

    code = "not_found_error"
    message = "Not found"


class ForbiddenException(BaseException):
    """Access forbidden exception (403 Forbidden)"""

    code = "forbidden_error"
    message = "Forbidden"


class TooManyRequestsException(BaseException):
    """Rate limit exceeded exception (429 Too Many Requests)"""

    code = "too_many_requests_error"
    message = "Too many requests"


class InternalServerException(BaseException):
    """Internal server error exception (500 Internal Server Error)"""

    code = "internal_server_error"
    message = "The server encountered an unexpected condition"


# Domain-specific exceptions
class TaskNotFoundException(NotFoundException):
    """Task not found in database"""

    code = "task_not_found"
    message = "Task not found"


class TaskAccessDeniedException(ForbiddenException):
    """User does not have access to this task"""

    code = "task_access_denied"
    message = "You do not have access to this task"


class InvalidTaskStatusTransitionException(BusinessException):
    """Invalid task status transition"""

    code = "invalid_status_transition"
    message = "Invalid task status transition"


class InvalidApiKeyException(UnauthorizedException):
    """Invalid or missing API key"""

    code = "invalid_api_key"
    message = "Invalid or missing API key"
