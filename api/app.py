import logging.config

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from tortoise.contrib.fastapi import register_tortoise

from api.misc.config import TORTOISE_ORM, config
from api.misc.fastapi import catch_exceptions_middleware, validation_exception_handler

# Import logging configuration FIRST to ensure it's applied before anything else
from api.misc.logging import LOG_LEVEL, LOGGING_CONFIG, get_logger

# Apply logging configuration immediately
logging.config.dictConfig(LOGGING_CONFIG)

from api.presentation.resources import health_router, tasks_router

# Initialize logger
logger = get_logger()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This function sets up:
    - FastAPI instance with metadata
    - API routers (health, tasks)
    - CORS middleware
    - Database connection (Tortoise ORM)
    - Exception handlers
    """
    app = FastAPI(
        title="Clean Architecture Example",
        description=(
            "Educational Tasks CRUD API demonstrating Clean Architecture principles.\n\n"
            "## Authentication\n"
            "Use the API key in the `X-API-Key` header.\n\n"
            f"**Default API Key:** `{config.DEFAULT_API_KEY}`\n\n"
            "Click the 🔒 Authorize button to set your API key for all requests."
        ),
        version="1.0.0",
        docs_url=None if config.is_production() else "/docs",
        redoc_url=None,
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(tasks_router)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Database registration
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,  # Use migrations instead
        add_exception_handlers=True,
    )

    # Exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.middleware("http")(catch_exceptions_middleware)

    return app


if __name__ == "__main__":
    uvicorn.run(
        "api.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=config.PORT,
        log_level=LOG_LEVEL.lower(),  # Use environment-aware log level
        reload=not config.is_production(),
    )
