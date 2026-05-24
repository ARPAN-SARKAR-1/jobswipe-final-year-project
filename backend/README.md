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

In production, set a strong `JWT_SECRET`, set `FRONTEND_URL` to the deployed frontend origin, and do not use wildcard CORS origins.

## Uploads

Files are stored under `backend/uploads` locally. The folder is gitignored except for `.gitkeep`. For production, move uploads to S3, Cloudinary, Supabase Storage, or another object storage provider and store the public URL in MySQL.

## Security Notes

- Password reset tokens are not returned in API responses.
- Access tokens expire after 30 minutes by default, and logout revokes the current token in the local/demo server process.
- Resume, profile image, and company logo uploads validate extension, MIME type, and size before saving.
- Resume PDFs are served through a protected API route with role and ownership checks.
- Swagger/OpenAPI docs are disabled in production.
- Login, forgot password, reset password, reports, and chat messages have basic in-memory rate limiting for local/demo protection.
- Redis-backed rate limiting, SMTP email, and cloud file storage are planned production improvements.
