import json

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.domain.exceptions import (
    BusinessException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
)
from api.misc.config import config
from api.misc.logging import get_logger
from api.presentation.responses import BaseResponse, ErrorResponse

# Use centralized logger
logger = get_logger()

# Business exceptions that should be logged as warnings, not errors
BUSINESS_EXCEPTIONS = (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    BusinessException,
    TooManyRequestsException,
)


async def catch_exceptions_middleware(request: Request, call_next):
    """
    Middleware to catch all exceptions and return them in envelope format.

    Business exceptions (4xx) are logged as warnings.
    Server errors (5xx) are logged as errors.
    """
    try:
        return await call_next(request)
    except UnauthorizedException as e:
        error_response = ErrorResponse(**e.serialize())
        status_code = status.HTTP_401_UNAUTHORIZED
    except NotFoundException as e:
        error_response = ErrorResponse(**e.serialize())
        status_code = status.HTTP_404_NOT_FOUND
    except BusinessException as e:
        error_response = ErrorResponse(**e.serialize())
        status_code = status.HTTP_400_BAD_REQUEST
    except ForbiddenException as e:
        error_response = ErrorResponse(**e.serialize())
        status_code = status.HTTP_403_FORBIDDEN
    except TooManyRequestsException as e:
        error_response = ErrorResponse(**e.serialize())
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    except InternalServerException as e:
        error_response = ErrorResponse(**e.serialize())
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    except Exception as e:
        # Catch all for unexpected errors
        if config.is_production():
            error_response = ErrorResponse(
                code="internal_server_error",
                message="An internal server error occurred.",
            )
        else:
            error_response = ErrorResponse(
                code="internal_server_error",
                message=str(e),
            )
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    response: BaseResponse = BaseResponse(
        success=False, data=None, error=error_response
    )

    # Log business exceptions as warnings, server errors as errors
    exception_instance = locals().get("e")
    if exception_instance and isinstance(exception_instance, BUSINESS_EXCEPTIONS):
        logger.warning(f"[fastapi] {error_response.code}: {error_response.message}")
    else:
        logger.error(f"[fastapi] {error_response.code}: {error_response.message}")

    return JSONResponse(content=response.model_dump(), status_code=status_code)


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors and return them in envelope format.
    """
    message, location = None, None
    errors_details = []

    for missing_param in exc.errors():
        if len(missing_param["loc"]) > 1:
            location = missing_param["loc"][1]
            message = missing_param.get("msg", "field_required")
        elif len(missing_param["loc"]) == 1:
            location = missing_param["loc"][0]
            message = missing_param.get("msg", "invalid_value")

        error_detail = {"message": message, "location": location}
        errors_details.append(error_detail)

    error = ErrorResponse(
        code="bad_request", message="Unprocessable entity", errors=errors_details
    )

    response: BaseResponse = BaseResponse(success=False, error=error, data=None)
    logger.warning(
        f"[fastapi] {error.code}: {error.message} - {json.dumps(errors_details)}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response.model_dump()
    )
