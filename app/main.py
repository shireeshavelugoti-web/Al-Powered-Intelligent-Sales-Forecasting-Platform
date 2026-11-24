# Defines API endpoints and handles requests.
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models
from .database import Base, sql_engine
from .routers import analysis, leads, outreach, scroing


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=sql_engine)
    yield


app = FastAPI(
    title="Sales AI",
    description="AI Sales Assistant and Lead Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan

)

# CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]

)

# REGISTER ROUTERS
app.include_router(leads.router)
app.include_router(analysis.router)
app.include_router(outreach.router)
app.include_router(scroing.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }