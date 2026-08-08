from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, HTMLResponse
import firebase_admin
from firebase_admin import credentials

from config import settings
from api.database import engine, Base
from api.utils.errors import APIException
from api.routers.auth import router as auth_router
from api.routers.account import router as account_router
from api.routers.user import router as user_router
from api.routers.notifications import router as notifications_router

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "message": exc.message
            }
        }
    )


@app.get("/", response_class=HTMLResponse, tags=["OBank site"])
async def get_site():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(user_router)
app.include_router(notifications_router)
