from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db.database import init_db
from .api.cases import router as cases_router
from .api.investigate import router as investigate_router
from .api.review import router as review_router
from .api.reports import router as reports_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize persistent SQLite/Postgres database
    init_db()
    if getattr(settings, "SEED_DEMO_DATA", False):
        from .db.database import SessionLocal
        from .db.repository import CaseRepository
        db = SessionLocal()
        try:
            CaseRepository.seed_benchmark_case(db)
        finally:
            db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Evidence-grounded accounts payable due-diligence platform | HackIIITD Esya '26",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware: Explicit trusted origins from configuration (no wildcard with credentials)
safe_cors_origins = [o for o in settings.CORS_ORIGINS if o != "*"]
if not safe_cors_origins:
    safe_cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=safe_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(cases_router, prefix="/api")
app.include_router(investigate_router, prefix="/api")
app.include_router(review_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for Render/Vercel and uptime monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "tinyfish_mode": "LIVE" if settings.TINYFISH_API_KEY else "SIMULATED",
        "rules_version": settings.RULES_VERSION,
        "database": "sqlite_persistent" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
    }

@app.get("/", tags=["root"])
async def root():
    return {
        "message": "VendorShield AI API is operational.",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
