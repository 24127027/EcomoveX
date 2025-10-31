import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db, engine
from models.destination import Destination


async def add_test_destination():
    """Add a test destination to the database"""
    async with engine.begin() as conn:
        # Get a session
        async_session = AsyncSession(engine, expire_on_commit=False)
        async with async_session as session:
            # Check if destination already exists
            existing = await session.get(Destination, 1)
            if existing:
                print("✓ Test destination already exists (ID: 1)")
                return

            # Create a test destination
            destination = Destination(
                longitude=-122.4194,
                latitude=37.7749
            )
            session.add(destination)
            await session.commit()
            await session.refresh(destination)
            print(f"✓ Test destination created (ID: {destination.id}, Location: {destination.latitude}, {destination.longitude})")


if __name__ == "__main__":
    print("Adding test data to database...")
    asyncio.run(add_test_destination())
    print("Done!")
