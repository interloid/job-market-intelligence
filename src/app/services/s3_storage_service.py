import json
import logging
from typing import Any

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class S3StorageService:
    def __init__(self, bucket_name: str, bucket_region: str):
        self.bucket_name = bucket_name
        self.bucket_region = bucket_region
        self.session = aioboto3.Session()

    async def upload_json(
        self,
        data: Any,
        object_key: str,
    ):

        json_data = json.dumps(
            data,
            ensure_ascii=False,
            default=str,
            indent=4,
        ).encode("utf-8")

        try:
            async with self.session.client(
                "s3",
                region_name=self.bucket_region,
            ) as s3_client:
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=json_data,
                    ContentType="application/json",
                )

            return object_key

        except (BotoCoreError, ClientError):
            logger.exception(
                "Failed to upload raw data to S3: %s",
                object_key,
            )
            raise
