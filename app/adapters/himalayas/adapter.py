import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

logger = logging.getLogger(__name__)


class HimalayasAdapter:
    @staticmethod
    async def fetch_rss_feed_records():

        try:
            url = "https://himalayas.app/jobs/rss"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)

                response.raise_for_status()
                http_status = response.status_code

                data = response.text

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning("Himalayas returned HTTP status=%s", status_code)
            raise

        except httpx.RequestError as exc:
            logger.warning(
                "Himalayas request failed: %s",
                exc,
                exc_info=True,
            )
            raise

        return data, http_status

    @staticmethod
    def parse_rss_feed_records(xml_data: str):

        try:
            root = ET.fromstring(
                xml_data,
                forbid_dtd=True,
                forbid_entities=True,
                forbid_external=True,
            )

        except ET.ParseError as exc:
            raise ValueError("Invalid RSS XML format") from exc

        except DefusedXmlException as exc:
            raise ValueError("Unsafe XML content detected") from exc

        channel = root.find("channel")

        if root.tag != "rss" or channel is None:
            raise ValueError("Invalid RSS feed structure")

        last_build_date = channel.findtext("lastBuildDate")

        return channel.findall("item"), last_build_date

    @staticmethod
    def convert_item_to_dict(item) -> dict:

        job_data: dict[str, Any] = {}

        field_mapping = {
            "companyName": "company_name",
        }

        for element in item:
            tag_name = element.tag.split("}")[-1]

            value = (
                element.text.strip() if element.text and element.text.strip() else None
            )

            if tag_name in {"description", "encoded"}:
                value = HimalayasAdapter.clean_html_content(value)

            if element.attrib and tag_name != "guid":
                value = {"text": value, "attributes": element.attrib}

            field_name = field_mapping.get(tag_name, tag_name)

            if field_name in job_data:
                if field_name == "guid":
                    continue

                if not isinstance(job_data[field_name], list):
                    job_data[field_name] = [job_data[field_name]]

                job_data[field_name].append(value)

            else:
                job_data[field_name] = value

        return job_data

    @staticmethod
    def clean_html_content(html_content: str | None) -> str | None:
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")

        return soup.get_text(separator=" ", strip=True)
