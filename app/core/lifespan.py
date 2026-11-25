from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import dispose_engine, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_engine()
    try:
        yield
    finally:
        await dispose_engine()
