# Swipe for Success Deployment Guide

This guide covers a production-style deployment with Vercel for the Next.js frontend, Render for the FastAPI backend, Railway MySQL for the database, and Cloudinary for uploaded files.

## Railway MySQL

1. Create a Railway project and add a MySQL service.
2. Copy the MySQL connection URL from Railway.
3. Use the PyMySQL SQLAlchemy format for the backend:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE
```

## Render Backend

Create a Render Web Service from the repository.

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

Required Render environment variables:

```env
ENV=production
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE
JWT_SECRET=<generate-a-long-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_URL=https://your-frontend.vercel.app
UPLOAD_DIR=uploads
CLOUDINARY_CLOUD_NAME=<cloudinary-cloud-name>
CLOUDINARY_API_KEY=<cloudinary-api-key>
CLOUDINARY_API_SECRET=<cloudinary-api-secret>
```

Do not add backend secrets to Vercel.

## Vercel Frontend

Create a Vercel project from the `frontend` directory.

Required Vercel environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com/api
```

## Cloudinary

1. Create a Cloudinary account.
2. Copy the cloud name, API key, and API secret into Render environment variables.
3. When all three Cloudinary variables are present, uploads go to Cloudinary.
4. If they are absent, local development continues to use `backend/uploads`.

Supported uploads:

- Job seeker profile images
- Job seeker resume PDFs
- Recruiter company logos

## Database Commands

Run migrations from the backend service shell or a local shell with production `DATABASE_URL`:

```powershell
alembic upgrade head
```

Optional demo data:

```powershell
python seed.py
```

## Common Errors

- CORS errors: confirm `FRONTEND_URL` exactly matches the Vercel origin, without a trailing path.
- Database connection errors: confirm Railway allows the Render service to connect and the `DATABASE_URL` uses `mysql+pymysql`.
- Upload errors: confirm all three Cloudinary variables are set in Render.
- Reset token exposure: set `ENV=production` so reset tokens are not returned in API responses.
- Frontend API errors: confirm `NEXT_PUBLIC_API_BASE_URL` ends with `/api`.

## Post-Deployment Checklist

- Open `https://your-backend.onrender.com/health` and confirm it returns `status: ok`.
- Open Render logs and confirm the backend starts without import errors.
- Run `alembic upgrade head`.
- Open the Vercel frontend and register a test user.
- Log in and verify role-based dashboard routing.
- Upload a profile image, resume PDF, and company logo.
- Confirm Cloudinary receives the uploaded files.
- Confirm the frontend can load uploaded Cloudinary URLs.
