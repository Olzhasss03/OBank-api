from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.database import engine, Base
from api.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from api.models import UserModel, AccountModel, TransactionModel

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

app = FastAPI(
    title="Oldtk",
    version="v1.0",
    lifespan=lifespan
)

app.include_router(auth_router)
