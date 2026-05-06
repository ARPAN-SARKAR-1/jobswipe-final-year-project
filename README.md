# JobSwipe

## Project Overview

JobSwipe is a modern full-stack final year project for job seekers, freshers, recruiters, admins, and an Owner account. Its main idea is to reduce job-search fatigue with a Tinder-style job discovery flow: one active job card at a time, swipe right to apply, swipe left to skip, and save jobs for later.

## Problem Statement

Freshers and early-career job seekers often spend too much time scrolling through repetitive listings. JobSwipe turns discovery into a focused workflow so users can quickly express intent, bookmark good roles, and track applications from one dashboard.

## Features

- Landing page with the tagline "Swipe Less. Apply Smarter."
- Register and login with JWT authentication, bcrypt password hashing, role redirects, validation, loaders, and toasts.
- Forgot password and reset password demo flow with development reset token return.
- Job Seeker dashboard, editable profile, profile picture upload, GitHub URL, education details, experience level, resume PDF upload, saved jobs, applications, and withdraw action.
- Swipe Jobs page with Framer Motion drag animation, reject, save, apply, undo, and progress indicator.
- Jobs list with job type, experience level, location, skill, work mode, and active-only filters.
- Recruiter dashboard, company profile, company logo upload, job posting, received applications, and application status updates.
- Admin dashboard with users, jobs, applications, swipes, moderation controls, and database summary cards.
- Owner hierarchy: the seeded Owner account can create and manage admins, while admins can moderate normal users and content without managing other admins.
- Recruiter verification so only verified recruiters can publish active jobs.
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

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, Framer Motion, Lucide icons, React Hot Toast.
- Backend: Python FastAPI, SQLAlchemy ORM, Alembic, Pydantic, JWT, bcrypt.
- Database: MySQL with PyMySQL.
- Local infrastructure: Docker Compose MySQL.

## Folder Structure

```text
jobswipe-python-final/
+-- docker-compose.yml
+-- README.md
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
ACCESS_TOKEN_EXPIRE_MINUTES=1440
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

## API Docs

Run the backend and open:

```text
http://localhost:8000/docs
```

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
- Analytics for recruiter job performance.
- Video interview scheduling.
- Advanced fraud detection for fake recruiters or suspicious posts.
- Exportable admin reports.

## Final Year Project Explanation

JobSwipe demonstrates a complete, deployable full-stack system with authentication, role-based access, CRUD operations, file uploads, relational data modeling, REST APIs, database migrations, and a distinctive swipe-based user experience. The project is suitable for explaining real-world job portal workflows while presenting a visually polished frontend and a maintainable Python backend.
