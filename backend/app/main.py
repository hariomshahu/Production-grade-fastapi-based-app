"""FastAPI app: CRUD API and optional static mount for local dev."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BIND_HOST, BIND_PORT
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown (e.g. for health)."""
    yield


app = FastAPI(title="Items API", lifespan=lifespan)

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
