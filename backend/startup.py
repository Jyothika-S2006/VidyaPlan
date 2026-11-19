"""Render startup script: init DB and load data before serving."""
import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup():
    sys.path.insert(0, ".")
    from app.db.session import AsyncSessionLocal, init_db
    from app.pipeline.load import load_data

    logger.info("Initialising database...")
    await init_db()

    logger.info("Loading data...")
    async with AsyncSessionLocal() as session:
        result = await load_data(session)
        logger.info("Data loaded: %s", result)


if __name__ == "__main__":
    asyncio.run(startup())
