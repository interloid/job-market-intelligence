import asyncio
import logging

from prefect import flow

from app.pipelines.remoteok_flow import remoteok_ingestion_flow
from app.pipelines.remoteok_task import fetch_due_sources

logger = logging.getLogger(__name__)


@flow(name="source_dispatcher_flow")
async def source_dispatcher_flow():

    due_sources = await fetch_due_sources()

    if not due_sources:
        logger.info("No sources are due for ingestion")
        return

    for source in due_sources:
        if source["source_code"] == "remoteok":
            logger.info("Starting RemoteOK ingestion")

            await remoteok_ingestion_flow()

        else:
            logger.warning(
                "No ingestion flow configured for source: %s",
                source["source_code"],
            )


if __name__ == "__main__":
    asyncio.run(source_dispatcher_flow())
