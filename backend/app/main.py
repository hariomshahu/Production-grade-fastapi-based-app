"""FastAPI app: CRUD API and optional static mount for local dev."""
import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import BIND_HOST, BIND_PORT
from app.routers import items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown (e.g. for health)."""
    yield


app = FastAPI(title="Items API", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log full traceback and return error detail so we can debug 500s (e.g. DynamoDB)."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router)


@app.get("/health")
def health():
    """ALB health check."""
    return {"status": "ok"}


# Optional: serve React build when running standalone (e.g. local dev)
_static = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _static.is_dir():
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="static")


def run():
    """Run with uvicorn (for gunicorn or direct)."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=BIND_HOST,
        port=BIND_PORT,
        reload=False,
    )


if __name__ == "__main__":
    run()
