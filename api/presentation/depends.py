from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader

from api.data.postgres_repositories import repo_get_client_by_api_key
from api.domain.entities import Client
from api.domain.exceptions import InvalidApiKeyException
from api.misc.logging import get_logger

# Initialize logger for authentication
logger = get_logger()

# Define the API Key security scheme for Swagger UI
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_client(
    x_api_key: Annotated[str | None, Depends(api_key_header)] = None
) -> Client:
    """
    Dependency to authenticate client via API key header.

    Validates the X-API-Key header and returns the authenticated client.

    Usage in endpoints:
        async def endpoint(*, client: ClientDep):
            # client is automatically injected and authenticated
            ...

    Raises:
        InvalidApiKeyException: If API key is missing or invalid
    """
    if not x_api_key:
        logger.warning(
            "[api.presentation.depends:get_current_client] Authentication failed: Missing API key"
        )
        raise InvalidApiKeyException()

    logger.info(
        "[api.presentation.depends:get_current_client] Authenticating client request"
    )

    client = await repo_get_client_by_api_key(api_key=x_api_key)

    if not client:
        logger.warning(
            "[api.presentation.depends:get_current_client] Authentication failed: Invalid or inactive API key"
        )
        raise InvalidApiKeyException()

    logger.info(
        f"[api.presentation.depends:get_current_client] Client {client.client_id} authenticated successfully"
    )

    return client


# Type alias for dependency injection
ClientDep = Annotated[Client, Depends(get_current_client)]
