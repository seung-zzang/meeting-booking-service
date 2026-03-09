import os
import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine

from appserver.apps.account.endpoints import router as account_router
from appserver.apps.calendar.endpoints import router as calendar_router
from appserver.admin import include_admin_views, AdminAuthentication
from .db import engine

app = FastAPI()

def include_routers(_app: FastAPI):
    _app.include_router(account_router)
    _app.include_router(calendar_router)
    
    _app.mount("/static", StaticFiles(directory="static"), name="static")
    _app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def init_middleware(_app: FastAPI):
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


include_routers(app)
init_middleware(app)


def init_admin(_app: FastAPI, _engine: AsyncEngine):
    return Admin(
        _app,
        _engine,
        base_url="/seungzzang/admin/",
        authentication_backend=AdminAuthentication("secret-key"),
    )


admin = init_admin(app, engine)
include_admin_views(admin)


def init_sentry(dsn: str | None = None):
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        integrations=[
            StarletteIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={403, *range(500, 600)},
                http_methods_to_capture=("GET", "POST", "DELETE", "PUT", "PATCH"),
            ),
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes={403, *range(500, 600)},
                http_methods_to_capture=("GET", "POST", "DELETE", "PUT", "PATCH"),
            ),
        ],
    )

init_sentry(os.getenv("SENTRY_DSN", "https://3752290a7226700d07b232b5d919cd10@o4510991165423616.ingest.us.sentry.io/4510991169093632"))