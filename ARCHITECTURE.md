# Architecture

## Overview

JobSwipe is a full-stack job portal with a Next.js frontend, FastAPI backend, SQLAlchemy ORM, Alembic migrations, and MySQL database.

```text
Frontend -> FastAPI -> SQLAlchemy -> MySQL
```

The frontend handles screens, forms, role-based navigation, upload validation, and user interactions. The backend handles authentication, authorization, business rules, database access, file upload validation, and moderation rules.

## Frontend Architecture

- `frontend/app`: Next.js App Router pages for login, signup, dashboards, jobs, companies, chats, notifications, privacy, and terms.
- `frontend/components`: Reusable UI components such as job cards, badges, headers, reports, timelines, and empty states.
- `frontend/lib`: API client, role redirects, upload validation, option lists, and utility functions.
- `frontend/hooks`: Client-side authentication guard and current user loading.
- `frontend/types`: Shared TypeScript types for API responses.

```text
Page -> Component -> apiFetch -> FastAPI endpoint
```

## Backend Architecture

- `backend/app/main.py`: FastAPI app setup, CORS, uploads static mount, and router registration.
- `backend/app/routers`: API groups for auth, jobs, applications, swipes, chats, notifications, reports, companies, recruiter, job seeker, and admin.
- `backend/app/models`: SQLAlchemy database models.
- `backend/app/schemas`: Pydantic request and response schemas.
- `backend/app/services`: Shared business services such as notifications, timelines, reviews, and rate limiting.
- `backend/app/utils`: Helpers for upload validation, matching, pagination, and skills.
- `backend/alembic`: Database migration history.

```text
Router -> Schema validation -> Role check -> Service/Model -> Database
```

## Database Architecture

MySQL stores users, profiles, companies, jobs, applications, swipes, chats, notifications, reports, reviews, timelines, and admin action logs. SQLAlchemy models define relationships and constraints, while Alembic manages schema changes.

```text
User -> Role-specific profile -> Jobs/Applications/Chats/Reports
Company -> Recruiters -> Jobs -> Applications
```

## API Flow

```text
Frontend action -> apiFetch -> FastAPI route -> Pydantic validation -> SQLAlchemy query -> MySQL -> JSON response
```

The frontend stores the JWT token in browser local storage and sends it as a bearer token for protected routes.

## Authentication Flow

```text
User -> Select role -> Login -> JWT token -> Protected API -> Current user
```

1. User selects Job Seeker, Recruiter, Admin, or Owner on login.
2. Backend verifies email, password, and selected role.
3. Backend returns JWT token and user details.
4. Frontend stores token and redirects based on the actual account role.
5. Protected APIs decode the JWT and load the current user.

## Role-Based Access Flow

```text
Request -> JWT Login -> Protected API -> Role Check -> Database action
```

- Owner can manage Admin accounts and access all moderation tools.
- Admin can moderate normal users, jobs, applications, companies, recruiters, reports, reviews, and chats.
- Recruiter can manage their own company profile, jobs, applications, and recruiter-started chats.
- Job Seeker can manage profile, swipe, apply, withdraw, save, report, and review eligible companies.

## Job Application Flow

```text
Job Seeker -> Public verified job -> Apply -> Application -> Timeline -> Recruiter review
```

Only public jobs from verified companies and verified recruiters appear in job seeker flows. Duplicate applications are blocked by backend checks and database constraints.

## Chat Flow

```text
Application -> Recruiter shortlist -> Recruiter starts chat -> Participants exchange messages
```

Job seekers cannot start chats. Recruiters can start chats only for their own shortlisted applications. Both participants can send messages after the recruiter starts the thread.

## Company And Recruiter Verification Flow

```text
Recruiter profile -> Company profile -> Pending -> Owner/Admin review -> Verified or Rejected
```

New companies and recruiters start as pending. Active job posting is allowed only when the recruiter account is active, the recruiter profile is verified, and the linked company is verified.

## Admin Moderation Flow

```text
Report or admin review -> Owner/Admin action -> Status update -> Notification -> Timeline/log
```

Owner/Admin users can review reports, pause or remove jobs, suspend users, pause applications, pause chats, verify companies, verify recruiters, and moderate company reviews.
