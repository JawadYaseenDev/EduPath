from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import admin, auth, catalogue, profile, recommendations, reference
from .config import get_settings
from .db import Base, SessionLocal, engine
from .seed import seed_demo, seed_dev_staff, seed_reference


def init_db() -> None:
    # Development convenience. Staging/production use Alembic migrations.
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_reference(db)
        settings = get_settings()
        if settings.load_demo_data:
            seed_demo(db)
        if settings.environment == "development" and settings.dev_staff_password:
            seed_dev_staff(db, settings.dev_staff_password)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="EduRecommend API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def friendly_validation_error(_: Request, exc: RequestValidationError):
    """Turn validation errors into one plain sentence the app can show directly."""
    first = exc.errors()[0] if exc.errors() else {}
    message = str(first.get("msg", "Please check your input."))
    message = message.removeprefix("Value error, ")
    field = ".".join(str(p) for p in first.get("loc", [])[1:])
    return JSONResponse(status_code=422,
                        content={"detail": message, "field": field or None})


@app.get("/health")
def health():
    return {"ok": True}


for module in (auth, reference, profile, catalogue, recommendations, admin):
    app.include_router(module.router)
app.include_router(profile.account)
