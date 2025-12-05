# Clean Architecture Example - Tasks CRUD API

An educational FastAPI project demonstrating Clean Architecture principles with a simple Tasks CRUD domain. This project serves as a learning resource for developers before working on the production API.

## Overview

This example implements a Task Management API with:

- **Clean Architecture** - Clear separation of domain, data, and presentation layers
- **Envelope Responses** - Consistent response format across all endpoints
- **API Key Authentication** - Simple header-based authentication
- **Exception Handling** - Middleware-based error handling with smart logging
- **Python** - Python 3.12 with type hints
- **Fly.io Ready** - Complete deployment configuration

## Features

- Create, read, update, delete tasks
- Filter tasks by status and priority
- API key-based client authentication
- Envelope response pattern (success/error/data)
- Comprehensive error handling
- FastAPI auto-generated documentation
- Docker and Docker Compose support
- Database migrations with Aerich
- Blue-green deployment on Fly.io

## Tech Stack

- **FastAPI** Web framework
- **Pydantic** Data validation
- **Tortoise ORM** - Async ORM for PostgreSQL
- **Aerich** - Database migrations
- **PostgreSQL** Database
- **Poetry** - Dependency management
- **Python** 3.12+

## Project Structure

```
example/
├── api/
│   ├── domain/              # Business logic layer
│   │   ├── entities.py      # Core business objects (Client, Task)
│   │   ├── enums.py         # Domain enumerations (TaskStatus, TaskPriority)
│   │   ├── exceptions.py    # Domain exceptions
│   │   ├── usecases.py      # Business use cases
│   │   └── postgres_adapters.py  # Model → Entity adapters
│   ├── data/                # Data access layer
│   │   ├── postgres_models.py    # Tortoise ORM models
│   │   ├── postgres_repositories.py  # Database operations
│   │   └── fakers.py        # Test data factories
│   ├── presentation/        # API layer
│   │   ├── resources.py     # API endpoints
│   │   ├── responses.py     # Response models (with envelope)
│   │   ├── validations.py   # Request models
│   │   └── depends.py       # FastAPI dependencies (auth)
│   ├── misc/                # Infrastructure
│   │   ├── config.py        # Configuration
│   │   └── fastapi.py       # Exception middleware
│   ├── migrations/          # Database migrations
│   ├── scripts/             # Deployment scripts
│   └── app.py               # FastAPI application
├── docker-compose.yml       # Local development setup
├── Dockerfile               # Container build
├── fly.toml                 # Fly.io deployment config
└── pyproject.toml           # Dependencies (Poetry)
```

## Domain Model

### Entities

**Client** - API key holder (for authentication)

- client_id, name, api_key, is_active
- Owns multiple tasks

**Task** - Main business entity

- task_id, title, description, status, priority, due_date
- Belongs to a client

### Enums

- **TaskStatus**: pending, in_progress, completed, cancelled
- **TaskPriority**: low, medium, high

### Business Rules

1. Tasks start with 'pending' status
2. Cannot reopen completed tasks
3. Tasks can only be accessed/modified by their owner client
4. API key authentication required for all task endpoints

## API Endpoints

All endpoints return responses in envelope format:

```json
{
  "success": true,
  "error": null,
  "data": { ... }
}
```

### Health

- `GET /health` - Health check (no auth required)

### Tasks (require X-API-Key header)

- `POST /tasks` - Create task
- `GET /tasks` - List tasks (with optional status/priority filters)
- `GET /tasks/{task_id}` - Get task by ID
- `PATCH /tasks/{task_id}` - Update task (partial update)
- `DELETE /tasks/{task_id}` - Delete task

## Prerequisites

- [Docker](https://www.docker.com/get-started/) and Docker Compose
- [Python 3.12+](https://www.python.org/downloads/release/python-312/) (for local development)
- [Poetry](https://python-poetry.org/docs/) (for local development)

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd example

# Copy environment file
cp .env.example .env
```

### 2. Start with Docker (Recommended)

```bash
# Build and start all services
docker compose up --build

# Or run in detached mode (background)
docker compose up --build -d

# Check service health
docker compose ps

# View logs
docker compose logs -f
```

This will start:

- **API Service**: <http://localhost:8000>
- **PostgreSQL Database**: localhost:5432

The startup process automatically:

- Creates database schemas
- Runs migrations
- Seeds a default test client with API key

### 3. Access Services

**Default API Key**: `dev-test-api-key-12345`

- **API Documentation (Swagger UI)**: <http://localhost:8000/docs>
  - Click the 🔒 **Authorize** button (top right)
  - Enter the API key: `dev-test-api-key-12345`
  - Click "Authorize" then "Close"
  - Now you can test all endpoints interactively with authentication included automatically

- **API Service**: <http://localhost:8000>
- **Health Check**: <http://localhost:8000/health/>

### 4. Useful Docker Commands

```bash
# Stop all services
docker compose down

# Restart a specific service
docker compose restart api

# View API service logs
docker compose logs api -f

# Access interactive shell in API container
docker compose exec api /bin/bash -l
```

## Development Setup

For development with Docker, follow the [Quick Start](#quick-start) above. The repository is mounted as a volume, so code changes will automatically reload the API server.

## Testing

This project uses **pytest** for testing and **Hypothesis** for property-based testing to ensure business logic works correctly across a wide range of inputs.

### Testing Strategy

The test suite includes:

1. **Property-Based Tests** (Hypothesis)
   - Generate hundreds of test cases automatically
   - Find edge cases you might not think of
   - Verify business rules hold for all valid inputs
   - Located in `api/domain/tests/test_usecases.py`

2. **Unit Tests**
   - Test individual functions and methods
   - Mock external dependencies
   - Fast execution, no database required

3. **Integration Tests** (marked with `@pytest.mark.use_db`)
   - Test database interactions
   - Use test database automatically created/destroyed per test
   - Test adapters and repositories

### Running Tests with Docker

**Option 1: One-off test runs**

```bash
# Run all tests
docker compose run --rm api pytest

# Run with coverage report
docker compose run --rm api pytest --cov

# Run specific test directory
docker compose run --rm api pytest api/domain/tests/

# Run specific test file
docker compose run --rm api pytest api/domain/tests/test_usecases.py

# Run only property-based tests
docker compose run --rm api pytest -k "hypothesis" -v
```

**Option 2: Interactive testing (recommended for development)**

This is the preferred method when actively developing - run tests in an interactive shell while services are running:

```bash
# Terminal 1: Start services (keep running)
docker compose up

# Terminal 2: Access interactive shell
docker compose exec api /bin/bash -l

# Inside container: Run tests as needed
pytest                                    # All tests
pytest --cov                              # With coverage
pytest api/domain/tests/                  # Specific directory
pytest -k "test_create_task"              # Specific test
pytest -v                                 # Verbose output
pytest --hypothesis-show-statistics       # See Hypothesis stats
```

### Understanding Hypothesis (Property-Based Testing)

Hypothesis automatically generates test data and finds edge cases. Instead of writing individual test cases, you define **properties** that should always be true.

**Example from our codebase:**

```python
@settings(max_examples=10)  # Generate 10 random test cases
@given(client=active_client_builder())  # Use Hypothesis strategy
async def test_create_task_generates_valid_task(client):
    """Property: Creating a task always generates a valid task with pending status."""
    # Test runs 10 times with different random clients
    # Hypothesis finds edge cases like empty names, special characters, etc.
```

**Why use Hypothesis?**

- Finds bugs you didn't know existed
- Tests with realistic data (not just "test1", "test2")
- Automatically shrinks failing cases to minimal examples
- Catches edge cases like empty strings, max values, Unicode, etc.

**Hypothesis Strategies** (`api/domain/tests/strategies.py`):

- `client_builder()` - Generates random Client entities
- `task_builder()` - Generates random Task entities
- `pending_task_builder()` - Tasks with pending status
- `client_with_tasks()` - Client with related tasks

### Test Factories

The project uses two factory patterns for creating test data:

1. **Pydantic Factories** (for domain entities)

   ```python
   from api.data.fakers import ClientFactory, TaskFactory

   client = ClientFactory.build()  # Create entity instance
   ```

2. **AsyncTortoiseFactory** (for database models)

   ```python
   from api.data.fakers import ClientPostgresFactory

   client = await ClientPostgresFactory.create()  # Creates in DB
   tasks = await TaskPostgresFactory.create_batch(5)  # Creates 5 tasks
   ```

### Test Markers

- `@pytest.mark.asyncio` - Required for async tests
- `@pytest.mark.use_db` - Test needs database access
- `@given()` - Hypothesis property-based test
- `@settings(max_examples=N)` - Control Hypothesis examples

### Test Configuration

**conftest.py** - Automatic test database setup:

- Tests marked with `@pytest.mark.use_db` get a fresh test database
- Database is created before test, destroyed after
- Uses `testdb` name to avoid conflicts

**Coverage Reports**:

```bash
# Generate HTML coverage report
docker compose run --rm api pytest --cov --cov-report=html

# View in browser (files saved to htmlcov/)
open htmlcov/index.html
```

## Code Quality & Development Workflow

This project uses automated code quality tools to maintain consistent, clean code. These tools run automatically before each commit via pre-commit hooks.

### Setting Up Pre-commit Hooks

Pre-commit hooks automatically check your code before allowing a commit. To set them up:

```bash
# Install pre-commit hooks (one-time setup)
poetry run pre-commit install

# The hooks will now run automatically on git commit
# They will:
# - Format code with Black
# - Sort imports with isort
# - Remove unused imports with autoflake
# - Check types with mypy
# - Fix trailing whitespace
# - Validate YAML files
# - Fix markdown formatting
```

### Running Code Quality Tools Manually

You can run these tools manually without committing:

```bash
# Run all pre-commit hooks on all files
poetry run pre-commit run --all-files

# Format code with Black
poetry run black .

# Sort imports
poetry run isort .

# Type checking
poetry run mypy api/

# Lint with Ruff
poetry run ruff check .
```

### What Each Tool Does

| Tool | Purpose | Educational Value |
|------|---------|-------------------|
| **Black** | Code formatter - enforces consistent style | Learn PEP 8 compliance without manual effort |
| **isort** | Import sorter - organizes imports | Understand Python import best practices |
| **mypy** | Static type checker - catches type errors | Learn type safety and prevent bugs |
| **autoflake** | Removes unused imports/variables | Keep code clean and minimal |
| **Ruff** | Fast Python linter - catches common issues | Learn Python idioms and best practices |

### Pre-commit Hook Workflow

When you run `git commit`, the hooks will:

1. Check and auto-fix your code
2. If fixes were made, the commit is aborted
3. Review the changes, stage them with `git add`
4. Commit again - hooks will pass this time

This ensures all committed code meets quality standards.

## Database

### Connecting with Database Clients

When the application is running with `docker compose up`, you can connect to the PostgreSQL database with any PostgreSQL client.

**Connection URL:**

```
postgres://tasks:tasks@localhost:5432/tasks_db
```

**Or use these individual connection parameters:**

- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `tasks_db`
- **User**: `tasks`
- **Password**: `tasks`

**Example with psql (command line):**

```bash
psql postgres://tasks:tasks@localhost:5432/tasks_db
```

### Database Migrations with Aerich

```bash
# Create new migration after model changes
docker compose exec api aerich migrate --name "describe_your_changes"

# Apply migrations
docker compose exec api aerich upgrade

# Rollback migration
docker compose exec api aerich downgrade
```

## API Usage

### Using cURL

1. **Health Check (no auth)**

   ```bash
   curl http://localhost:8000/health
   ```

2. **Create Task**

   ```bash
   curl -X POST http://localhost:8000/tasks/ \
     -H "X-API-Key: dev-test-api-key-12345" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Learn Clean Architecture",
       "description": "Study this example project",
       "priority": "high"
     }'
   ```

3. **List Tasks**

   ```bash
   curl http://localhost:8000/tasks/ \
     -H "X-API-Key: dev-test-api-key-12345"
   ```

4. **Get Task**

   ```bash
   curl http://localhost:8000/tasks/{task_id}/ \
     -H "X-API-Key: dev-test-api-key-12345"
   ```

5. **Update Task**

   ```bash
   curl -X PATCH http://localhost:8000/tasks/{task_id}/ \
     -H "X-API-Key: dev-test-api-key-12345" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "in_progress"
     }'
   ```

6. **Delete Task**

   ```bash
   curl -X DELETE http://localhost:8000/tasks/{task_id}/ \
     -H "X-API-Key: dev-test-api-key-12345"
   ```

### Using Swagger UI

The easiest way to test the API is through the interactive Swagger UI:

1. Navigate to <http://localhost:8000/docs>
2. Click the 🔒 **Authorize** button (top right corner)
3. Enter the API key: `dev-test-api-key-12345`
4. Click "Authorize" then "Close"
5. All subsequent requests will automatically include the API key

## Clean Architecture

This project is following the [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) software design philosophy.

![Clean Architecture Diagram](clean_architecture.jpg)

### Layers Explained

1. **Domain Layer** (`api/domain/`)
   - Pure business logic
   - No dependencies on frameworks or databases
   - Contains: entities, enums, use cases, exceptions

2. **Data Layer** (`api/data/`)
   - Database models and repositories
   - Adapters to convert between models and entities
   - Abstracts data access from business logic

3. **Presentation Layer** (`api/presentation/`)
   - HTTP endpoints and request/response models
   - Authentication dependencies
   - Converts HTTP requests to use case calls

4. **Infrastructure** (`api/misc/`)
   - Configuration, logging, middleware
   - Framework-specific code

### Modules

#### Entities

`domain/entities.py` - Entities are native business objects. In this project, examples are **Client** and **Task**. An entity is typically saved to the database using a repository method (see below).

`domain/enums.py` - We use enums to guarantee the uniqueness of constant values. Examples: **TaskStatus**, **TaskPriority**.

#### Adapters

`domain/postgres_adapters.py` - The adapters are functions that convert a database model to an entity. For example, `task_postgres_adapter()` converts a `TaskPostgres` model to a `Task` entity. In this way, the database is abstracted from the business logic.

#### Repositories

`data/postgres_repositories.py` - These functions receive entities and change the database in a specific way. The functions that return entities typically use an adapter to convert the model instance to an entity. Examples: `repo_create_task()`, `repo_get_task_by_id()`.

#### Use Cases

`domain/usecases.py` - The use cases contain the actual business logic. For example, what happens when someone creates a task? The use case validates ownership, applies business rules (like "cannot reopen completed tasks"), and raises exceptions. The use cases typically call repository methods. Examples: `create_task()`, `update_task()`.

#### Exceptions

`domain/exceptions.py` - Exceptions are typically raised by use cases. They can be converted to JSON and returned to the HTTP client via the exception middleware. Examples: `TaskNotFoundException`, `TaskAccessDeniedException`, `InvalidTaskStatusTransitionException`.

#### Resources

`presentation/resources.py` - API endpoints are built using FastAPI. They use validations to parse HTTP payloads, call the use cases, check authentication, and serialize responses using the envelope pattern. Examples: `create_task_resource()`, `list_tasks_resource()`.

#### Validations

`presentation/validations.py` - Endpoint payload validations are built using the Pydantic library. They are used by FastAPI to parse and validate the request data. Examples: `CreateTaskRequest`, `UpdateTaskRequest`.

#### Responses

`presentation/responses.py` - Endpoint JSON responses are built using the Pydantic library. They are used by FastAPI to serialize them. All responses use the envelope pattern with `BaseResponse[DataResponse]`. Examples: `TaskResponse`, `TaskListResponse`.

### Key Patterns

- **Dependency Inversion**: Domain doesn't depend on data or presentation
- **Repository Pattern**: Abstract data access through interfaces
- **Adapter Pattern**: Convert between different layer representations
- **Use Case Pattern**: Each business operation is a separate function
- **Envelope Pattern**: Consistent response structure across all endpoints

## Database Migrations

### Create Migration

```bash
# After modifying models in postgres_models.py
docker-compose exec api aerich migrate --name "describe_your_changes"
```

### Apply Migrations

```bash
docker-compose exec api aerich upgrade
```

### Rollback Migration

```bash
docker-compose exec api aerich downgrade
```

## Testing

### Run Tests

```bash
# With docker-compose
docker-compose exec api pytest

# With coverage
docker-compose exec api pytest --cov=api --cov-report=term-missing

# Locally with Poetry
poetry run pytest
```

### Test Markers

- `@pytest.mark.use_db` - Tests that need database access

## Deployment to Fly.io

### Prerequisites

- Fly.io account
- Fly CLI installed

### Steps

1. **Login to Fly.io**

   ```bash
   flyctl auth login
   ```

2. **Create Fly app**

   ```bash
   flyctl apps create clean-architecture-example
   ```

3. **Create Postgres database**

   ```bash
   flyctl postgres create --name clean-architecture-db
   flyctl postgres attach --app clean-architecture-example clean-architecture-db
   ```

4. **Set secrets**

   ```bash
   flyctl secrets set ENVIRONMENT=production
   ```

5. **Deploy**

   ```bash
   flyctl deploy
   ```

6. **Check status**

   ```bash
   flyctl status
   flyctl logs
   ```

### Deployment Features

- **Blue-Green Deployment**: Zero-downtime deployments
- **Health Checks**: Automatic health monitoring at `/health`
- **Auto Migrations**: Migrations run automatically on deploy
- **Auto Scaling**: Can scale to 0 machines when idle

## Learning Resources

### For New Developers

1. **Start Here**: Read this README top to bottom
2. **Explore the Code**:
   - Start with `api/domain/entities.py` - understand the domain
   - Then `api/domain/usecases.py` - see business logic
   - Then `api/presentation/resources.py` - see HTTP layer
3. **Try It Out**:
   - Use docker-compose to run locally
   - Test endpoints with Swagger UI
   - Read the request/response flow
4. **Understand the Patterns**:
   - Follow a request from endpoint → use case → repository
   - See how exceptions flow through middleware
   - Notice how entities are separate from database models

### Key Concepts Demonstrated

- ✅ Clean Architecture layers
- ✅ Dependency Inversion Principle
- ✅ Repository Pattern
- ✅ Use Case Pattern
- ✅ Adapter Pattern
- ✅ Envelope Response Pattern
- ✅ Exception Handling
- ✅ API Key Authentication
- ✅ Request Validation (Pydantic)
- ✅ Database Migrations
- ✅ Docker & Docker Compose
- ✅ Fly.io Deployment

## Comparison with Production API

| Feature | This Example | Production API |
|---------|--------------|----------------|
| Architecture | Clean Architecture | Clean Architecture |
| Domains | Single (Tasks) | Multiple (Auth, Portfolio, etc.) |
| Authentication | API Key | JWT + Session (Redis) |
| Response Format | Envelope | Envelope |
| Exception Handling | Middleware | Middleware |
| Database | Postgres | Postgres |
| ORM | Tortoise | Tortoise |
| Testing | Unit tests | Unit + Integration |
| Deployment | Fly.io | Fly.io |

## Contributing

This is an educational example. Feel free to experiment and modify it for learning purposes. If you find any issues or have suggestions, please open an issue or pull request.
