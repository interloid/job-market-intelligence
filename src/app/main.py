from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import dispose_engine, get_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_engine()
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    return {"Fastapi is running"}
