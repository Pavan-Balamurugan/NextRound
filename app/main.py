from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import Base, engine
from app.routers import auth, companies, experiences, profile, ai
from app.schemas import HealthResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Placement Prep Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(experiences.router)
app.include_router(profile.router)
app.include_router(ai.router)


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(demo_mode=settings.demo_mode)


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/app.js")
def appjs():
    return FileResponse(STATIC_DIR / "app.js")


@app.get("/styles.css")
def css():
    return FileResponse(STATIC_DIR / "styles.css")
