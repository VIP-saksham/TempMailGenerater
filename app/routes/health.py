import time
from fastapi import APIRouter
from ..config import settings

router = APIRouter(tags=["health"])
_START = time.time()


@router.get("/health")
def health():
    return {"ok": True, "app": settings.app_name, "uptime_seconds": round(time.time() - _START, 2)}


@router.get("/")
def root():
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")
