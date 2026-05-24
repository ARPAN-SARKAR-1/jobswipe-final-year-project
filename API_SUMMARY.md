# API Summary

Base local API URL:

```text
http://localhost:8000/api
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## Auth

- `POST /auth/register`: Public signup for Job Seeker and Recruiter accounts.
- `POST /auth/login`: Role-based login with email, password, and selected role.
- `POST /auth/logout`: Revokes the current JWT for the local/demo server process.
- `GET /auth/me`: Returns the current authenticated user.
- `POST /auth/forgot-password`: Generates password reset instructions without exposing the token in the response.
- `POST /auth/reset-password`: Resets password using a valid reset token.

## Jobs

- `GET /jobs`: Lists public verified jobs with filters and pagination.
- `GET /jobs/feed`: Job seeker swipe feed.
- `GET /jobs/{job_id}`: Public job detail if the job is visible.
- `POST /jobs`: Recruiter creates a job if recruiter and company are verified.
- `PUT /jobs/{job_id}`: Recruiter updates own job.
- `DELETE /jobs/{job_id}`: Recruiter deactivates own job.

## Applications

- `POST /applications`: Job seeker applies to a job.
- `GET /applications/my`: Job seeker views own applications.
- `PUT /applications/{application_id}/withdraw`: Job seeker withdraws own application.
- `GET /applications/{application_id}/timeline`: Shows application timeline for allowed users.

## Swipes

- `POST /swipes`: Job seeker records LIKE, REJECT, or SAVE.
- `GET /swipes/history`: Job seeker views swipe history.
- `POST /swipes/undo`: Job seeker undoes latest swipe.
- `DELETE /swipes/saved/{job_id}`: Removes a saved job.

## Chats

- `POST /chats/start`: Recruiter starts chat for own shortlisted application.
- `GET /chats`: Lists chat threads for the current recruiter or job seeker.
- `GET /chats/{thread_id}/messages`: Lists messages for chat participants or moderators.
- `POST /chats/{thread_id}/messages`: Sends message as a chat participant.
- `PUT /chats/{thread_id}/read`: Marks messages as read.

## Notifications

- `GET /notifications`: Lists current user's notifications.
- `GET /notifications/unread-count`: Returns unread notification count.
- `PUT /notifications/read-all`: Marks all current user's notifications as read.
- `PUT /notifications/{notification_id}/read`: Marks one notification as read.

## Protected Files

- `GET /files/resumes/{filename}`: Serves resume PDFs only after JWT, role, and ownership checks.

## Reports

- `POST /reports/job/{job_id}`: Job seeker reports a job.
- `POST /reports/recruiter/{recruiter_id}`: Job seeker reports a recruiter.

## Admin And Owner

- `GET /admin/dashboard`: Owner/Admin summary.
- `GET /admin/users`: Paginated user list for moderation.
- `GET /admin/jobs`: Paginated job list for moderation.
- `GET /admin/applications`: Paginated application list for moderation.
- `GET /admin/chats`: Paginated chat thread list for moderation.
- `GET /admin/reports`: Paginated report list.
- `PUT /admin/reports/{report_id}/status`: Updates report status.
- `POST /admin/admins`: Owner creates an admin account.
- `PUT /admin/admins/{admin_id}/suspend`: Owner suspends admin.
- `PUT /admin/admins/{admin_id}/activate`: Owner activates admin.
- `PUT /admin/admins/{admin_id}/remove`: Owner soft-removes admin.
- `PUT /admin/users/{user_id}/suspend`: Owner/Admin suspends normal user.
- `PUT /admin/users/{user_id}/activate`: Owner/Admin activates normal user.
- `PUT /admin/jobs/{job_id}/pause`: Owner/Admin pauses job.
- `PUT /admin/jobs/{job_id}/activate`: Owner/Admin activates job moderation status.
- `PUT /admin/jobs/{job_id}/remove`: Owner/Admin removes job from public flow.
- `PUT /admin/applications/{application_id}/pause`: Owner/Admin pauses application.
- `PUT /admin/applications/{application_id}/activate`: Owner/Admin activates application.
- `PUT /admin/chats/{thread_id}/pause`: Owner/Admin pauses chat.
- `PUT /admin/chats/{thread_id}/activate`: Owner/Admin activates chat.

## Company

- `GET /companies`: Public company list with pagination.
- `GET /companies/{company_id}`: Public company detail with recruiters and active jobs.
- `GET /companies/{company_id}/reviews`: Public visible company reviews.
- `POST /companies/{company_id}/reviews`: Job seeker reviews company after applying to a job from that company.

## Recruiter

- `GET /recruiter/dashboard`: Recruiter dashboard summary.
- `GET /recruiter/company-profile`: Recruiter company/profile details.
- `PUT /recruiter/company-profile`: Recruiter updates company/profile details.
- `POST /recruiter/company-logo`: Recruiter uploads company logo.
- `GET /recruiter/applications`: Recruiter views applications for own jobs.
- `PUT /recruiter/applications/{application_id}/status`: Recruiter updates own application status.

## Company And Recruiter Verification

- `GET /admin/companies`: Owner/Admin company verification list.
- `PUT /admin/companies/{company_id}/verify`: Owner/Admin verifies company.
- `PUT /admin/companies/{company_id}/reject`: Owner/Admin rejects company.
- `GET /admin/recruiters`: Owner/Admin recruiter verification list.
- `PUT /admin/recruiters/{recruiter_id}/verify`: Owner/Admin verifies recruiter.
- `PUT /admin/recruiters/{recruiter_id}/reject`: Owner/Admin rejects recruiter.

## Reviews

- `GET /admin/company-reviews`: Owner/Admin review moderation list.
- `PUT /admin/company-reviews/{review_id}/hide`: Owner/Admin hides review from public page.
- `PUT /admin/company-reviews/{review_id}/show`: Owner/Admin shows review publicly again.
