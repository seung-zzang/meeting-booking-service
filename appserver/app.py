from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from appserver.apps.account.endpoints import router as account_router
from appserver.apps.calendar.endpoints import router as calendar_router
from sqladmin import Admin
from appserver.db import engine
from sqlalchemy.ext.asyncio import AsyncEngine
from appserver.admin import include_admin_views, AdminAuthentication


app = FastAPI()

def include_routers(_app: FastAPI):
    _app.include_router(account_router)
    _app.include_router(calendar_router)

include_routers(app)


def init_admin(_app: FastAPI, _engine: AsyncEngine):
    return Admin(_app,
                 _engine,
                base_url="/seungzzang/admin/",
                authentication_backend=AdminAuthentication("secret-key")
                )

admin = init_admin(app, engine)
include_admin_views(admin)


def init_middleware(_app: FastAPI):
    _app.add_middleware(
        CORSMiddleware,
        # allow_origins=["*"],
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

init_middleware(app)