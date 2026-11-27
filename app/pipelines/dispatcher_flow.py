import asyncio
import logging
from uuid import UUID

from prefect import flow

from app.pipelines.common_task import fetch_due_sources
from app.pipelines.himalayas_flow import himalayas_ingestion_flow
from app.pipelines.remoteok_flow import remoteok_ingestion_flow

logger = logging.getLogger(__name__)


@flow(name="source_dispatcher_flow")
async def source_dispatcher_flow():

    due_sources = await fetch_due_sources()

    if not due_sources:
        logger.info("No sources are due for ingestion")
        return

    for source in due_sources:
        source_code = source["source_code"]
        try:
            if source_code == "remoteok":
                logger.info("Starting RemoteOK ingestion")

                await remoteok_ingestion_flow(
                    source_id=UUID(source["source_id"]),
                )
            elif source_code == "himalayas":
                logger.info("Starting himalayas ingestion")

                await himalayas_ingestion_flow(source_id=UUID(source["source_id"]))

            else:
                logger.warning(
                    "No ingestion flow configured for source: %s",
                    source["source_code"],
                )
        except Exception:
            logger.exception(
                "Ingestion failed for source: %s",
                source_code,
            )


if __name__ == "__main__":
    asyncio.run(source_dispatcher_flow())
