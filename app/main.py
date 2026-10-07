from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import init_db
from app.services.certificate_service import ensure_certificate_template
from app.api.routes import jobs_router, certificates_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan handler."""
    # Startup actions: initialize database tables & certificate template
    init_db()
    ensure_certificate_template()
    yield
    # Shutdown actions (if any)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Bulk Certificate Generator API for generating recipient certificates asynchronously.",
    lifespan=lifespan
)

# Include routes under /api/v1
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(certificates_router, prefix=settings.API_V1_STR)

# Also include routes under top-level /jobs and /certificates for compatibility with both URI styles
app.include_router(jobs_router)
app.include_router(certificates_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint returning system status."""
    return {"status": "ok"}
