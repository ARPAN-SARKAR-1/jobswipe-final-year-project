# JobSwipe Backend

FastAPI backend for JobSwipe. It uses MySQL, SQLAlchemy ORM, Alembic migrations, JWT authentication, bcrypt password hashing, and local file uploads for development.

## Setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

The app reads `.env` when present and falls back to `.env.example` for local demos.

## Uploads

Files are stored under `backend/uploads` locally. The folder is gitignored except for `.gitkeep`. For production, move uploads to S3, Cloudinary, Supabase Storage, or another object storage provider and store the public URL in MySQL.
