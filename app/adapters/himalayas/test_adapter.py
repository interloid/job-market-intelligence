import asyncio

from app.adapters.himalayas.adapter import HimalayasAdapter


async def main():

    xml_data = await HimalayasAdapter.fetch_rss_feed_records()

    records = HimalayasAdapter.parse_rss_feed_records(xml_data)

    print("Total RSS records:", len(records))

    for item in records[:1]:
        job_data = HimalayasAdapter.convert_item_to_dict(item)
        print(job_data)


if __name__ == "__main__":
    asyncio.run(main())
