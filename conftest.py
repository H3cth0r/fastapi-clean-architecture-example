import asyncpg
import pytest
from tortoise import Tortoise

from api.misc.config import config


async def drop_database_if_exists():
    connection = await asyncpg.connect(dsn=f"{config.TEST_POSTGRES_BASE_URL}/postgres")

    result = await connection.fetchval(
        f"SELECT 1 FROM pg_database WHERE datname = 'testdb'"
    )
    if result:
        await connection.execute(f'DROP DATABASE IF EXISTS "testdb"')
    await connection.close()


@pytest.fixture(autouse=True)
async def initialize_test_db(request):
    if "use_db" in request.keywords:
        await drop_database_if_exists()

        await Tortoise.init(
            db_url=f"{config.TEST_POSTGRES_BASE_URL}/testdb",
            _create_db=True,
            modules={"models": ["api.data.postgres_models"]},
        )
        await Tortoise.generate_schemas()

        yield

        await Tortoise._drop_databases()
    else:
        yield
