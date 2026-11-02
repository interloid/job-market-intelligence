import asyncio

from app.adapters.remoteok.adapter import RemoteOkAdapter


async def main():

    valid_records, invalid_records, skipped_records = await RemoteOkAdapter.run()

    print(f"Valid records: {len(valid_records)}")
    print(f"Invalid records: {len(invalid_records)}")
    print(f"Skipped records: {len(skipped_records)}")

    if valid_records:
        print(valid_records[0].model_dump())


if __name__ == "__main__":
    asyncio.run(main())
