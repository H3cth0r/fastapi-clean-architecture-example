"""
Seed script to initialize default client for development.

This script creates a default client with the API key from environment variables.
It's safe to run multiple times - it will skip if the client already exists.
"""

import asyncio
from uuid import uuid4

from tortoise import Tortoise

from api.data.postgres_models import ClientPostgres
from api.misc.config import TORTOISE_ORM, config


async def seed_default_client():
    """Create default client for development/testing."""
    print("🌱 Starting seed process...")

    # Initialize Tortoise
    await Tortoise.init(config=TORTOISE_ORM)

    # Generate database schemas if they don't exist
    await Tortoise.generate_schemas()

    try:
        # Check if a client with this API key already exists
        existing_client = await ClientPostgres.filter(
            api_key=config.DEFAULT_API_KEY
        ).first()

        if existing_client:
            print(f"✅ Default client already exists: {existing_client.name}")
            print(f"   API Key: {config.DEFAULT_API_KEY}")
            return

        # Create new default client
        client = await ClientPostgres.create(
            client_id=uuid4(),
            name="Default Development Client",
            api_key=config.DEFAULT_API_KEY,
            is_active=True,
        )

        print(f"✅ Created default client: {client.name}")
        print(f"   Client ID: {client.client_id}")
        print(f"   API Key: {config.DEFAULT_API_KEY}")
        print("\n📝 Use this API key in Swagger UI at http://localhost:8000/docs")

    except Exception as e:
        print(f"❌ Error during seed: {e}")
        raise
    finally:
        await Tortoise.close_connections()


def main():
    """Entry point for seed script."""
    asyncio.run(seed_default_client())


if __name__ == "__main__":
    main()
