# JobSwipe - Swipe-Based Job Portal

## Project Overview

JobSwipe is a modern full-stack final year project for job seekers, freshers, recruiters, admins, and an Owner account. Its main idea is to reduce job-search fatigue with a Tinder-style job discovery flow: one active job card at a time, swipe right to apply, swipe left to skip, and save jobs for later.

## Problem Statement

Freshers and early-career job seekers often spend too much time scrolling through repetitive listings. JobSwipe turns discovery into a focused workflow so users can quickly express intent, bookmark good roles, and track applications from one dashboard.

## Project Objective

The objective of JobSwipe is to build a secure, role-based job portal that supports job discovery, verified recruiter/company posting, applications, controlled recruiter-started chat, reports, notifications, and Owner/Admin moderation in one complete full-stack system.

## Features

- Landing page with the tagline "Swipe Less. Apply Smarter."
- Register and role-based login with JWT authentication, bcrypt password hashing, role redirects, validation, loaders, and toasts.
- Forgot password and reset password flow with token hidden from API responses.
- Job Seeker dashboard, editable profile, profile picture upload, GitHub URL, education details, experience level, resume PDF upload, saved jobs, applications, and withdraw action.
- Swipe Jobs page with Framer Motion drag animation, reject, save, apply, undo, and progress indicator.
- Jobs list with job type, experience level, location, skill, work mode, and active-only filters.
- Recruiter dashboard, company profile, recruiter profile, company logo upload, job posting, received applications, and application status updates.
- Admin dashboard with users, jobs, applications, swipes, company verification, recruiter verification, review moderation, moderation controls, and database summary cards.
- Owner hierarchy: the seeded Owner account can create and manage admins, while admins can moderate normal users and content without managing other admins.
- Separate company profiles with multiple recruiter profiles under one company.
- Company and recruiter verification with blue tick badges for trusted employers and recruiters.
- Company ratings and reviews from eligible job seekers.
- Fake job prevention rules so public jobs require a verified company, verified recruiter, active recruiter account, active job, valid deadline, and active moderation status.
- Recruiter verification so only verified recruiters under verified companies can publish active jobs.
- Company bond/service agreement disclosure on job cards, job details, saved jobs, applications, and swipe cards.
- Skill multi-select with removable skill chips and custom skills for job seeker profiles and job posts.
- Recruiter-started chat that becomes available only after an application is shortlisted.
- In-app notifications for application status changes, chat, reports, verification, and moderation events.
- Job and recruiter reporting workflow with Admin/Owner review and moderation actions.
- Match score for job seekers based on skills, experience, preferred job type, location, and work mode.
- Application timeline showing applied, viewed, shortlisted, withdrawn, chat started, and admin moderation events.
- Duplicate application prevention with clear status feedback.
- Privacy Policy and Terms & Conditions pages linked from signup and the footer.
- Local uploads stored in `backend/uploads` for development.

## Security Highlights

- Passwords are hashed with bcrypt/passlib before storage.
- JWT authentication protects logged-in API routes.
- Access tokens expire after 30 minutes by default, and logout revokes the current token for the local/demo server process.
- Role-based access control separates Owner, Admin, Recruiter, and Job Seeker permissions.
- Resource endpoints combine role checks with ownership checks to reduce BOLA/IDOR risk.
- Password reset tokens are not exposed in API responses; in development, the token can be checked only from backend debug logs.
- File uploads validate MIME type, file extension, and size before saving.
- Sensitive auth, report, and chat message endpoints use basic in-memory rate limiting for local/demo safety.
- Resume PDFs are served through a protected file route and are visible to recruiters only after a job seeker applies to their job.
- Recruiter and company verification helps prevent fake jobs from appearing publicly.
- In production, the backend requires a strong `JWT_SECRET` and does not allow wildcard CORS origins.
- Swagger/OpenAPI documentation is disabled in production.
- Email delivery for password resets, cloud file storage, upload scanning, and Redis-backed rate limiting are planned future improvements.

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, Framer Motion, Lucide icons, React Hot Toast.
- Backend: Python FastAPI, SQLAlchemy ORM, Alembic, Pydantic, JWT, bcrypt.
- Database: MySQL with PyMySQL.
- Local infrastructure: Docker Compose MySQL.

## Architecture Summary

```text
Frontend -> FastAPI -> SQLAlchemy -> MySQL
```

```text
User -> JWT Login -> Protected API -> Role Check -> Database
```

- The frontend is a Next.js application with role-specific pages and reusable components.
- The backend is a FastAPI application organized by routers, schemas, models, services, and utilities.
- SQLAlchemy models define relationships and constraints, while Alembic manages schema migrations.
- JWT authentication protects private APIs, and role checks separate Owner, Admin, Recruiter, and Job Seeker actions.
- Company and recruiter verification rules prevent untrusted public job posts.

## Folder Structure

```text
jobswipe-python-final/
+-- docker-compose.yml
+-- README.md
+-- SECURITY_NOTES.md
+-- TESTING_CHECKLIST.md
+-- DEVELOPMENT_NOTES.md
+-- ARCHITECTURE.md
+-- DATABASE_SCHEMA.md
+-- API_SUMMARY.md
+-- DEMO_SCRIPT.md
+-- VIVA_PREP.md
+-- backend/
|   +-- app/
|   |   +-- main.py
|   |   +-- core/
|   |   +-- models/
|   |   +-- schemas/
|   |   +-- routers/
|   |   +-- services/
|   |   +-- repositories/
|   |   +-- utils/
|   |   +-- exceptions/
|   +-- alembic/
|   +-- uploads/
|   +-- requirements.txt
|   +-- seed.py
|   +-- .env.example
|   +-- README.md
+-- frontend/
    +-- app/
    +-- components/
    +-- hooks/
    +-- lib/
    +-- public/
    +-- types/
    +-- .env.example
    +-- package.json
```

## MySQL Setup

```powershell
docker compose up -d
```

The compose file creates:

- `MYSQL_DATABASE=jobswipe`
- `MYSQL_USER=jobswipe_user`
- `MYSQL_PASSWORD=jobswipe_password`
- `MYSQL_ROOT_PASSWORD=root_password`
- MySQL exposed on port `3306`

## Backend Setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

The backend reads `.env` when present and falls back to `.env.example` for local demos.

Backend API: `http://localhost:8000`

Swagger docs: `http://localhost:8000/docs`

## Frontend Setup

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`

## Environment Variables

Backend `.env.example`:

```env
DATABASE_URL=mysql+pymysql://jobswipe_user:jobswipe_password@localhost:3306/jobswipe
JWT_SECRET=change_this_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=uploads
FRONTEND_URL=http://localhost:3000
ENV=development
```

Frontend `.env.example`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

Do not commit real `.env` files. Use platform environment variables in deployment.

## Alembic Commands

```powershell
cd backend
alembic upgrade head
alembic revision --autogenerate -m "describe change"
alembic downgrade -1
```

## Seed Commands

```powershell
cd backend
python seed.py
```

The seed script creates one protected Owner, one normal admin, two job seekers, two recruiters, fifteen jobs, sample applications, and sample swipes.
It also creates verified and pending company/recruiter examples plus a sample company review.

## Demo Credentials

- Owner: `owner@jobswipe.dev` / `Owner@123`
- Admin: `admin@jobswipe.dev` / `Admin@123`
- Job Seeker: `jobseeker@jobswipe.dev` / `Jobseeker@123`
- Recruiter: `recruiter@jobswipe.dev` / `Recruiter@123`

## Owner And Admin Hierarchy

- Public signup only creates Job Seeker and Recruiter accounts.
- Public signup cannot create Admin or Owner accounts, even if a request body is manually modified.
- The Owner account is created from seed data and marked as protected.
- The protected Owner account cannot be suspended or removed.
- Owner can create new admins from the Admin Dashboard.
- Owner can suspend, activate, or soft-remove normal admin accounts.
- Admins can moderate recruiters, job seekers, jobs, and applications.
- Admins cannot create admins, manage other admins, or change Owner permissions.
- Owner and Admin can both pause, activate, and remove jobs, and pause or activate applications.

## Company Profiles And Verification

- A company profile is a separate employer record. Multiple recruiter profiles can belong to the same company.
- Company records store name, logo, type, industry, website, official email domain, description, headquarters, founded year, size, registration number, verification status, rating totals, and audit fields.
- Recruiter profiles store the recruiter user, company, designation, department, official email, recruiter verification status, verification note, verifier, and verification time.
- New companies and recruiters start as `PENDING`.
- Owner/Admin users verify or reject companies from the Admin Dashboard.
- Owner/Admin users verify or reject recruiters from the Admin Dashboard.
- A verified company receives a blue tick and a "Verified Company" badge.
- A verified recruiter can receive a blue tick or verified badge beside trusted job information.
- Rejected or pending companies cannot publish public trusted jobs.
- Recruiters see clear warnings when their company or recruiter profile is pending or rejected.

## Role-Based Login

- The login page asks users to choose Job Seeker, Recruiter, Admin, or Owner before entering email and password.
- Login succeeds only when the selected role matches the account role in the database.
- Wrong role selection returns a clean "No account found for the selected role or credentials." error.
- Successful login redirects by the actual stored role.
- Public signup still allows only Job Seeker and Recruiter accounts.
- Admin and Owner accounts cannot be created through public signup.

## Company Reviews And Ratings

- Logged-in Job Seekers can review a company only after applying to at least one job from that company.
- Each job seeker can review a company once.
- Ratings are limited to 1 through 5.
- Review text is optional.
- Company average rating and total visible reviews update whenever reviews are created, hidden, or shown.
- Owner/Admin users can hide or show reviews from the Admin Dashboard.

## Fake Job Prevention

- A recruiter can publish an active job only when the recruiter account is active, the recruiter profile is verified, the company exists, and the company is verified.
- The backend links new jobs to the recruiter's verified company and ignores fake company names in job-posting requests.
- Job seeker job lists, swipe feed, job details, applications, and swipe actions only use public jobs from verified companies and verified recruiters.
- Owner/Admin users can still inspect all jobs, including paused, removed, pending, rejected, or unverified records.

## Matching And Duplicate Safety

- Match score is rule-based weighted scoring using skills, experience level, job type, location, and work mode. It is not a machine learning model.
- Duplicate applications are blocked so one job seeker cannot apply to the same job more than once.
- Duplicate company reviews are blocked so one job seeker can review one company only once.

## API Docs

Run the backend and open:

```text
http://localhost:8000/docs
```

## Supporting Documentation

- `SECURITY_NOTES.md`: Security decisions, upload validation, password reset behavior, rate limiting, CORS, and future hardening.
- `TESTING_CHECKLIST.md`: Manual test cases with test IDs, steps, expected results, and status column.
- `DEVELOPMENT_NOTES.md`: Professional development process summary.
- `ARCHITECTURE.md`: Frontend, backend, database, API, authentication, role, application, chat, verification, and moderation flows.
- `DATABASE_SCHEMA.md`: Major models, fields, and relationships.
- `API_SUMMARY.md`: Key API groups and endpoints.
- `DEMO_SCRIPT.md`: 10-minute demo flow with speaking lines.
- `VIVA_PREP.md`: Common mentor questions and short answers.

## Privacy And Terms

- Public signup requires acceptance of both Terms & Conditions and Privacy Policy.
- The Privacy Policy explains collected data, profile details, application activity, swipe activity, chat messages, and file upload visibility.
- Resume PDFs are not public. A resume becomes visible to a recruiter only when the job seeker applies to that recruiter's job.
- Owner/Admin users may access records for moderation or support when required.
- The Terms page explains user responsibilities, recruiter posting rules, bond disclosure, moderation rights, and project/demo limitations.

## Deployment Guide

Frontend and backend are separated for independent deployment:

- Deploy frontend to Vercel.
- Deploy backend to Render, Railway, Fly.io, or a VPS.
- Use a managed MySQL database or platform MySQL add-on.
- Set `DATABASE_URL`, `JWT_SECRET`, `FRONTEND_URL`, and upload-related configuration through environment variables.
- For production uploads, replace local `backend/uploads` with S3, Cloudinary, Supabase Storage, or equivalent object storage.

## Future Scope

- SMTP email delivery for password resets.
- Resume parsing and skill matching.
- Cloud file storage with signed URLs.
- Redis-backed rate limiting for multi-instance production deployments.
- Automated company verification workflows.
- Advanced machine-learning-based recommendation.
- Analytics for recruiter job performance.
- Video interview scheduling.
- Advanced fraud detection for fake recruiters or suspicious posts.
- Exportable admin reports.

## Final Year Project Explanation

JobSwipe demonstrates a complete, deployable full-stack system with authentication, role-based access, CRUD operations, file uploads, relational data modeling, REST APIs, database migrations, and a distinctive swipe-based user experience. The project is suitable for explaining real-world job portal workflows while presenting a visually polished frontend and a maintainable Python backend.
