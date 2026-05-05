from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from storyforge.infrastructure.persistence import init_db
from storyforge.interfaces.api.v1 import analyst_router, cocreation_router, daemon_router, dissect_router, novel_router, planner_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="StoryForge", version="0.4.8", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dissect_router)
app.include_router(cocreation_router)
app.include_router(planner_router)
app.include_router(analyst_router)
app.include_router(daemon_router)
app.include_router(novel_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
