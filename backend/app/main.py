from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.cases import router as cases_router
from .api.investigate import router as investigate_router
from .api.review import router as review_router
from .api.reports import router as reports_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Evidence-grounded accounts payable due-diligence platform | HackIIITD Esya '26",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # Allow preview environments
    allow_credentials=True,
    allow_methods=["*"],
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
        "rules_version": settings.RULES_VERSION
    }

@app.get("/", tags=["root"])
async def root():
    return {
        "message": "VendorShield AI API is operational.",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
