# Database Schema Summary

## User

Purpose: Stores all platform accounts.

Important fields: `id`, `name`, `email`, `password_hash`, `role`, `account_status`, `accepted_terms`, `accepted_privacy`, `is_protected_owner`.

Relationships: User can have one JobSeekerProfile, one RecruiterProfile, many Jobs as recruiter, many Applications as job seeker, many Swipes, many Notifications, many Reports, and many CompanyReviews.

## Company

Purpose: Stores employer/company profiles separate from recruiter accounts.

Important fields: `id`, `company_name`, `company_logo_url`, `company_type`, `industry`, `website`, `official_email_domain`, `description`, `headquarters_location`, `verification_status`, `average_rating`, `total_reviews`.

Relationships: Company has many RecruiterProfiles, many Jobs, and many CompanyReviews.

## RecruiterProfile

Purpose: Stores recruiter-specific professional details and company membership.

Important fields: `id`, `user_id`, `company_id`, `designation`, `department`, `official_email`, `recruiter_verification_status`, `verification_note`, `verified_by_admin_id`, `verified_at`.

Relationships: RecruiterProfile belongs to one User and one Company. A company can have many recruiter profiles.

## JobSeekerProfile

Purpose: Stores job seeker profile details used for applications and match score.

Important fields: `id`, `user_id`, `phone`, `github_url`, `education`, `degree`, `college`, `passing_year`, `skills`, `experience_level`, `preferred_location`, `preferred_job_type`, `resume_pdf_url`.

Relationships: JobSeekerProfile belongs to one User.

## Job

Purpose: Stores recruiter-created job posts.

Important fields: `id`, `recruiter_id`, `company_id`, `title`, `company_name`, `location`, `job_type`, `work_mode`, `salary`, `required_skills`, `required_experience_level`, `deadline`, `is_active`, `has_bond`, `bond_years`, `bond_details`, `moderation_status`.

Relationships: Job belongs to one recruiter User and one Company. Job has many Applications, Swipes, ChatThreads, and Reports.

## Application

Purpose: Stores job seeker applications.

Important fields: `id`, `job_seeker_id`, `job_id`, `resume_pdf_url`, `github_url`, `status`, `admin_status`, `admin_note`.

Relationships: Application belongs to one Job Seeker and one Job. Application can have one ChatThread and many ApplicationTimeline events.

## Swipe

Purpose: Stores job seeker swipe actions.

Important fields: `id`, `job_seeker_id`, `job_id`, `action`, `created_at`.

Relationships: Swipe belongs to one Job Seeker and one Job.

## ChatThread

Purpose: Stores one controlled chat thread for a shortlisted application.

Important fields: `id`, `application_id`, `recruiter_id`, `job_seeker_id`, `job_id`, `status`, `started_by_recruiter`.

Relationships: ChatThread belongs to one Application, one recruiter User, one job seeker User, and one Job. ChatThread has many ChatMessages.

## ChatMessage

Purpose: Stores individual chat messages.

Important fields: `id`, `thread_id`, `sender_id`, `message_text`, `is_read`, `read_at`, `created_at`.

Relationships: ChatMessage belongs to one ChatThread and one sender User.

## Notification

Purpose: Stores in-app notifications.

Important fields: `id`, `user_id`, `title`, `message`, `type`, `is_read`, `link_url`.

Relationships: Notification belongs to one User.

## Report

Purpose: Stores job seeker reports against jobs or recruiters.

Important fields: `id`, `reporter_id`, `job_id`, `recruiter_id`, `report_type`, `description`, `status`, `admin_note`.

Relationships: Report belongs to one reporter User. It can link to one Job and/or one recruiter User.

## CompanyReview

Purpose: Stores job seeker ratings and reviews for companies.

Important fields: `id`, `company_id`, `job_seeker_id`, `rating`, `review_text`, `is_visible`.

Relationships: CompanyReview belongs to one Company and one Job Seeker. One job seeker can review a company once.

## ApplicationTimeline

Purpose: Stores application history events.

Important fields: `id`, `application_id`, `action`, `old_status`, `new_status`, `note`, `created_by_user_id`.

Relationships: ApplicationTimeline belongs to one Application and can link to the User who caused the event.

## AdminActionLog

Purpose: Stores moderation and owner/admin activity records.

Important fields: `id`, `admin_id`, `action_type`, `target_type`, `target_id`, `reason`, `created_at`.

Relationships: AdminActionLog belongs to the admin or owner User who performed the action.

## Relationship Summary

```text
Company has many Recruiters.
Company has many Jobs.
Job has many Applications.
Application can have one ChatThread.
ChatThread has many ChatMessages.
Job Seeker has many Applications.
Job Seeker has many Swipes.
Job Seeker can review a Company after applying to one of its Jobs.
Owner/Admin actions are recorded in AdminActionLog.
```
