# Swipe for Success Deployment Guide

This guide covers a production-style deployment with Vercel for the Next.js frontend, Render for the FastAPI backend, Railway MySQL for the database, and Cloudinary for uploaded files.

## Railway MySQL

1. Create a Railway project and add a MySQL service.
2. Copy the MySQL connection URL from Railway.
3. Use the PyMySQL SQLAlchemy format for the backend:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE
```

For Render, use the Railway public TCP proxy host and port. Do not use `mysql://`, `mysql.railway.internal`, any `*.railway.internal` host, `localhost`, or `127.0.0.1` in production. The backend validates `ENV=production` at startup and raises `Invalid production DATABASE_URL. Use mysql+pymysql://...` when the production database URL is missing or unsafe.

## Render Backend

Create a Render Web Service from the repository.

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

Required Render environment variables:

```env
ENV=production
DATABASE_URL=mysql+pymysql://USER:PASSWORD@PUBLIC_TCP_HOST:PUBLIC_TCP_PORT/DATABASE
JWT_SECRET=<generate-a-long-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_URL=https://your-frontend.vercel.app
UPLOAD_DIR=uploads
CLOUDINARY_CLOUD_NAME=<cloudinary-cloud-name>
CLOUDINARY_API_KEY=<cloudinary-api-key>
CLOUDINARY_API_SECRET=<cloudinary-api-secret>
CAPTCHA_ENABLED=true
EMAIL_VERIFICATION_REQUIRED=true
TWOFA_REQUIRED_ROLES=OWNER,ADMIN,RECRUITER
EMAIL_PROVIDER=smtp
EMAIL_FROM=no-reply@example.com
RESEND_API_KEY=<resend-api-key-if-using-resend>
SMTP_HOST=<smtp-host-if-using-smtp>
SMTP_PORT=587
SMTP_USER=<smtp-user-if-using-smtp>
SMTP_PASSWORD=<smtp-password-if-using-smtp>
OTP_EXPIRE_MINUTES=5
OTP_MAX_ATTEMPTS=5
EMAIL_OTP_RESEND_COOLDOWN_SECONDS=60
CAPTCHA_EXPIRE_MINUTES=5
TRUSTED_DEVICE_DAYS=30
TRUSTED_DEVICE_COOKIE_NAME=swipe_trusted_device
OWNER_EMAILS=owner1@example.com,owner2@example.com
ADMIN_EMAILS=admin@example.com
SUPPORT_EMAIL=support@example.com
INITIAL_TEAM_PASSWORD=<temporary-team-password>
RESET_TEAM_PASSWORDS=false
```

Do not add backend secrets to Vercel.

## Vercel Frontend

Create a Vercel project from the `frontend` directory.

Required Vercel environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com/api
```

For the live Swipe for Success backend, the value should be:

```env
NEXT_PUBLIC_API_BASE_URL=https://swipe-for-success-backend.onrender.com/api
```

The CAPTCHA request should resolve to `https://swipe-for-success-backend.onrender.com/api/auth/captcha?purpose=login`.

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

Production owner/admin team accounts are seeded from Render environment variables. Set `OWNER_EMAILS` and `ADMIN_EMAILS` as comma-separated lists, set `INITIAL_TEAM_PASSWORD` to a temporary password, and keep `RESET_TEAM_PASSWORDS=false` unless you intentionally want to rotate those team account passwords. With `ENV=production`, `python seed.py` creates or verifies only the configured team accounts, marks them active and email verified, and does not overwrite existing passwords unless `RESET_TEAM_PASSWORDS=true`. Demo users and sample jobs remain development-only.

`SUPPORT_EMAIL` is the support/sender address. Use the same address for `EMAIL_FROM` when appropriate, but it is not created as a login user by the seed script.

Everyone seeded with `INITIAL_TEAM_PASSWORD` must change that temporary password after first login. Owner and Admin accounts still require login OTP/2FA because `TWOFA_REQUIRED_ROLES` includes `OWNER,ADMIN,RECRUITER`.

Seed command:

```powershell
python seed.py
```

## Common Errors

- CORS errors: confirm `FRONTEND_URL` exactly matches the Vercel origin, without a trailing path.
- Database connection errors: confirm Railway allows the Render service to connect and the `DATABASE_URL` uses `mysql+pymysql` with the public TCP proxy, not `mysql://`, `mysql.railway.internal`, `localhost`, or `127.0.0.1`.
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
