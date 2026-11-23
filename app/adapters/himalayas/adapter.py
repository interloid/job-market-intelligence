import httpx
import logging

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

logger = logging.getLogger(__name__)


class HimalayasAdapter:
    
    @staticmethod
    async def fetch_rss_feed_records():
        
        try:
            url = 'https://himalayas.app/jobs/rss'
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    timeout=30.0
                )
                
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
        
        return data
        
        
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

        return channel.findall("item")
    
    
    @staticmethod
    def convert_item_to_dict(item) -> dict:
        
        job_data = {}
        
        for element in item:
            
            job_data[element.tag] = (
                element.text.strip()
                if element.text and element.text.strip()
                else None
            )
        
        return job_data
        
        
