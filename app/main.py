import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import Base, engine, SessionLocal
from .models import MailInbox
from .routes import health, mail

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("app")


async def cleanup_loop():
    """purges expired inboxes on an interval."""
    while True:
        try:
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                deleted = (
                    db.query(MailInbox)
                    .filter(MailInbox.expires_at < now)
                    .delete(synchronize_session=False)
                )
                db.commit()
                if deleted:
                    log.info("cleanup: removed %d expired inbox(es)", deleted)
            finally:
                db.close()
        except Exception as e:
            log.error("cleanup error: %s", e)
        await asyncio.sleep(settings.cleanup_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting %s in %s", settings.app_name, settings.app_env)
    Base.metadata.create_all(bind=engine)
    if os.path.isdir("app/static"):
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    log.info("shutting down")


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan, docs_url="/api/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(health.router)
app.include_router(mail.router)
