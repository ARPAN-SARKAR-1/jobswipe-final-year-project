# Demo Script

## 10-Minute Presentation Flow

### 1. Open Homepage

Action: Open `http://localhost:3000`.

Speaking line: "JobSwipe is a role-based job portal designed to reduce repetitive job searching through a swipe-based discovery workflow."

### 2. Explain Problem Statement

Action: Show the homepage and briefly explain the project idea.

Speaking line: "Freshers often scroll through many repeated job listings. JobSwipe is not trying to replace large job portals like Naukri or LinkedIn; it is a swipe-based fresher job discovery prototype focused on reducing fatigue and improving trust."

### 3. Login As Owner

Action: Open login page, select Owner, and login with demo Owner credentials.

Speaking line: "The login page requires users to choose their role first. This prevents a user from logging in through the wrong profile type."

### 4. Verify Company And Recruiter

Action: Open Admin Dashboard. Show Company Claims, Join Requests, Suspicious Jobs, Company Verification, and Recruiter Verification sections.

Speaking line: "Trust architecture is harder than feature architecture. That is why JobSwipe uses company claim verification, recruiter verification, fake-job risk scoring, and admin review queues before jobs become trusted."

### 5. Login As Recruiter

Action: Logout and login as Recruiter.

Speaking line: "Recruiters work under a company profile. If a verified company already exists, a recruiter must request to join it instead of creating a duplicate company name."

### 6. Post A Verified Job With Bond And Skills

Action: Open recruiter job posting page. Create a job with required skills and bond details.

Speaking line: "Active job posting is allowed only when the recruiter account is active, the recruiter is approved under a verified company, and the company itself is verified."

Optional trust demo: Create or show a job containing phrases such as "pay joining fee" or "security deposit".

Speaking line: "This rule-based risk scoring engine is not full ML. It checks safety signals and sends risky jobs to Owner/Admin review so job seekers do not see unsafe posts."

### 7. Login As Job Seeker

Action: Logout and login as Job Seeker.

Speaking line: "The job seeker dashboard shows profile completion, saved jobs, applications, and recommended jobs."

### 8. Complete Academic Profile

Action: Open profile page and show Academic Status, undergraduate fields, graduate fields, skills, GitHub, profile picture, and resume upload.

Speaking line: "The role remains Job Seeker, but the profile supports both Undergraduate and Graduate candidates. Undergraduate users can add current year, stream, CGPA, internship preference, marksheets, and certificates."

Action: Upload a resume, marksheet, and skill-linked certificate.

Speaking line: "Documents are not public. Recruiters can see them only after the candidate applies to that recruiter's job."

### 9. Swipe And Apply

Action: Open Swipe Jobs and swipe right on a verified job.

Speaking line: "A right swipe creates an application. A left swipe skips the job, and save stores it for later."

### 10. Show Duplicate Application Prevention

Action: Try applying again to the same job from job details or jobs list.

Speaking line: "The backend blocks duplicate applications, so one job seeker cannot apply to the same job more than once."

### 11. Show Company And Recruiter Reviews

Action: Open a company profile, show the rating summary, then open a recruiter profile from the recruiter list.

Speaking line: "Only candidates who have applied can review a company or recruiter. Reviews capture work culture, interview process, salary transparency, communication, response time, professionalism, and transparency."

Action: Submit a company review and recruiter review as an eligible job seeker.

Speaking line: "Anonymous reviews hide the candidate name publicly, but Owner/Admin users can still see reviewer identity for moderation."

### 12. Recruiter Shortlists

Action: Login as Recruiter and open Applications Received. Filter applicants by academic status, stream, CGPA, skills, or certificate availability, then change an application status to Shortlisted.

Speaking line: "Recruiters can view academic profile and certificates only for candidates who applied to their own jobs, then shortlist suitable candidates for chat."

### 13. Recruiter Starts Chat

Action: Click Start Chat after shortlisting.

Speaking line: "Chat is controlled. The recruiter must start it, and it is available only after the application is shortlisted."

### 14. Job Seeker Replies

Action: Login as Job Seeker and reply in Messages.

Speaking line: "After the recruiter starts the conversation, both participants can exchange messages."

### 15. Job Seeker Reports Job Or Recruiter

Action: Open a job card and submit a report.

Speaking line: "Job seekers can report unsafe jobs or recruiters. Reports go to Owner/Admin moderation."

### 16. Owner/Admin Handles Report

Action: Login as Admin or Owner, open Reports, update report status, and optionally pause/remove job.

Speaking line: "Moderators can review reports, pause jobs, remove jobs, suspend users, and record actions for accountability."

### 17. Show Review Analytics And Moderation

Action: Open Admin Dashboard, show Review Analytics, then hide or flag a seeded review.

Speaking line: "The review analytics section highlights highest-rated companies, lowest-rated companies, most-reviewed companies, low-rated recruiters, and hidden or flagged reviews."

### 18. Show Notifications, Timeline, Privacy, And Terms

Action: Open Notifications, Application Timeline, Privacy Policy, and Terms & Conditions.

Speaking line: "The platform keeps users informed through notifications and timeline events. Privacy and terms explain data use, resume visibility, moderation, and user responsibilities."

## Closing Line

"JobSwipe demonstrates a complete full-stack fresher job discovery prototype with secure authentication, role-based authorization, company claim verification, recruiter approval, fake job risk scoring, file upload validation, applications, chat, moderation, and presentation-ready documentation."

## Cold-Start Demo Note

Speaking line: "Because this is a final year prototype, we use seeded verified companies and sample jobs to demonstrate how the platform behaves after onboarding. The real-market cold-start problem would require company partnerships, recruiter onboarding, and continuous trust operations."
