# Development Notes

## Development Process

JobSwipe started as a local prototype focused on proving the main job discovery idea: a swipe-based workflow for job seekers and a recruiter dashboard for job posting and application review.

After the core modules became stable, the clean working version was prepared for GitHub with environment files, uploads, build output, dependency folders, and local cache files excluded from version control.

Later improvements were handled through structured fixes. The work focused on security, role protection, verification workflows, upload safety, documentation, and presentation readiness without changing the main project direction.

## Major Modules Developed

- Authentication with JWT login, signup, logout, forgot password, and reset password.
- Role-based access for Owner, Admin, Recruiter, and Job Seeker users.
- Swipe system for job discovery, save, reject, apply, and undo.
- Job posting with skills, job type, work mode, deadline, salary, and bond details.
- Applications with duplicate prevention, withdraw action, status updates, and timeline history.
- Company and recruiter verification with trusted badges and posting restrictions.
- Admin and Owner moderation for users, jobs, applications, reports, companies, recruiters, reviews, and chats.
- Recruiter-started chat after shortlisting.
- Reports for unsafe jobs or recruiters.
- Notifications for important actions and moderation updates.
- Privacy Policy and Terms & Conditions pages.

## Repository Approach

The project history should be presented honestly. It was built and refined locally first, then the clean project state was prepared for repository upload. Documentation and security fixes were added as structured improvements after mentor review.

No commit history should be described beyond what is actually present in the repository.

## Current Presentation State

The project now has working frontend and backend modules, database migrations, seed data, role-based demo accounts, API documentation through Swagger, and supporting project documents for explanation, testing, database relationships, architecture, and viva preparation.
