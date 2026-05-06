from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import admin, applications, auth, chats, jobs, jobseeker, notifications, recruiter, reports, swipes

app = FastAPI(
    title="JobSwipe API",
    description="FastAPI backend for the JobSwipe swipe-based job and internship portal.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(jobseeker.router, prefix="/api")
app.include_router(recruiter.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(swipes.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(chats.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "JobSwipe API is running", "docs": "/docs"}
