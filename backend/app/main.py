from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import admin, applications, auth, chats, companies, files, jobs, jobseeker, notifications, recruiter, recruiters, reports, security, swipes

app = FastAPI(
    title="JobSwipe API",
    description="FastAPI backend for the JobSwipe swipe-based job and internship portal.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = settings.upload_path
for public_subfolder in ("profile-pictures", "company-logos"):
    public_dir = upload_path / public_subfolder
    public_dir.mkdir(parents=True, exist_ok=True)
    app.mount(f"/uploads/{public_subfolder}", StaticFiles(directory=public_dir), name=f"uploads-{public_subfolder}")

app.include_router(auth.router, prefix="/api")
app.include_router(security.router, prefix="/api")
app.include_router(jobseeker.router, prefix="/api")
app.include_router(recruiter.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(recruiters.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(swipes.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(chats.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    docs_path = "/docs" if not settings.is_production else "disabled in production"
    return {"message": "JobSwipe API is running", "docs": docs_path}
