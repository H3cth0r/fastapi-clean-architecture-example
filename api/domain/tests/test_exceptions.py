"""
Tests for domain exceptions.
"""

from api.domain.exceptions import (
    BaseException,
    BusinessException,
    ForbiddenException,
    InternalServerException,
    InvalidApiKeyException,
    InvalidTaskStatusTransitionException,
    NotFoundException,
    TaskAccessDeniedException,
    TaskNotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
)


def test_base_exception_serialize_without_detail():
    """Test that BaseException serializes correctly without detail."""
    exc = BaseException()
    result = exc.serialize()

    assert result == {"code": "error", "message": ""}
    assert "detail" not in result


def test_base_exception_serialize_with_detail():
    """Test that BaseException serializes correctly with detail."""
    exc = BaseException(detail="This is additional detail")
    result = exc.serialize()

    assert result == {
        "code": "error",
        "message": "",
        "detail": "This is additional detail",
    }


def test_business_exception_serialization():
    """Test BusinessException serialization."""
    exc = BusinessException(detail="Business rule violated")
    result = exc.serialize()

    assert result == {
        "code": "business_error",
        "message": "Business error",
        "detail": "Business rule violated",
    }


def test_unauthorized_exception_serialization():
    """Test UnauthorizedException serialization."""
    exc = UnauthorizedException(detail="Token expired")
    result = exc.serialize()

    assert result["code"] == "unauthorized_error"
    assert result["message"] == "Unauthorized"
    assert result["detail"] == "Token expired"


def test_not_found_exception_serialization():
    """Test NotFoundException serialization."""
    exc = NotFoundException(detail="Resource ID not found")
    result = exc.serialize()

    assert result["code"] == "not_found_error"
    assert result["message"] == "Not found"
    assert result["detail"] == "Resource ID not found"


def test_forbidden_exception_serialization():
    """Test ForbiddenException serialization."""
    exc = ForbiddenException(detail="Insufficient permissions")
    result = exc.serialize()

    assert result["code"] == "forbidden_error"
    assert result["message"] == "Forbidden"
    assert result["detail"] == "Insufficient permissions"


def test_too_many_requests_exception_serialization():
    """Test TooManyRequestsException serialization."""
    exc = TooManyRequestsException(detail="Rate limit: 100 req/min")
    result = exc.serialize()

    assert result["code"] == "too_many_requests_error"
    assert result["message"] == "Too many requests"
    assert result["detail"] == "Rate limit: 100 req/min"


def test_internal_server_exception_serialization():
    """Test InternalServerException serialization."""
    exc = InternalServerException(detail="Database connection failed")
    result = exc.serialize()

    assert result["code"] == "internal_server_error"
    assert result["message"] == "The server encountered an unexpected condition"
    assert result["detail"] == "Database connection failed"


def test_task_not_found_exception_serialization():
    """Test TaskNotFoundException serialization."""
    exc = TaskNotFoundException(detail="Task ID: 123")
    result = exc.serialize()

    assert result["code"] == "task_not_found"
    assert result["message"] == "Task not found"
    assert result["detail"] == "Task ID: 123"


def test_task_access_denied_exception_serialization():
    """Test TaskAccessDeniedException serialization."""
    exc = TaskAccessDeniedException(detail="Task belongs to another user")
    result = exc.serialize()

    assert result["code"] == "task_access_denied"
    assert result["message"] == "You do not have access to this task"
    assert result["detail"] == "Task belongs to another user"


def test_invalid_task_status_transition_exception_serialization():
    """Test InvalidTaskStatusTransitionException serialization."""
    exc = InvalidTaskStatusTransitionException(
        detail="Cannot move from completed to pending"
    )
    result = exc.serialize()

    assert result["code"] == "invalid_status_transition"
    assert result["message"] == "Invalid task status transition"
    assert result["detail"] == "Cannot move from completed to pending"


def test_invalid_api_key_exception_serialization():
    """Test InvalidApiKeyException serialization."""
    exc = InvalidApiKeyException(detail="API key format invalid")
    result = exc.serialize()

    assert result["code"] == "invalid_api_key"
    assert result["message"] == "Invalid or missing API key"
    assert result["detail"] == "API key format invalid"
