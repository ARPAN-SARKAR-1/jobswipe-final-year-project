# Viva Preparation

## Top Mentor Questions And Short Answers

1. What is JobSwipe?
   - JobSwipe is a full-stack job portal where job seekers discover jobs through a swipe-based interface and recruiters manage jobs, applications, and chats under verified companies.

2. Why did you choose this project?
   - Job searching can be repetitive and unfocused for freshers. This project solves that with a faster discovery workflow and clear application tracking.

3. What is unique about JobSwipe?
   - It combines swipe-based job discovery with role-based dashboards, company verification, recruiter verification, controlled chat, reports, notifications, and admin moderation.

4. What frontend technology did you use?
   - Next.js, TypeScript, Tailwind CSS, Framer Motion, Lucide icons, and React Hot Toast.

5. Why Next.js?
   - Next.js provides structured routing, fast development, production build support, and a clean way to organize pages and components.

6. Why TypeScript?
   - TypeScript helps catch type errors early and makes API response handling safer.

7. What backend technology did you use?
   - Python FastAPI with SQLAlchemy ORM, Alembic migrations, Pydantic schemas, and JWT authentication.

8. Why FastAPI?
   - FastAPI is fast, modern, supports automatic API documentation, and works well with Pydantic validation.

9. Why MySQL?
   - MySQL is reliable for relational data such as users, companies, jobs, applications, reviews, and chats.

10. What is SQLAlchemy used for?
    - SQLAlchemy maps Python models to database tables and manages database queries.

11. What is Alembic used for?
    - Alembic manages database schema migrations in a structured way.

12. How does JWT authentication work?
    - After login, the backend creates a signed JWT containing the user ID and role. Protected APIs read the bearer token, validate it, and load the current user.

13. How is role-based access protected?
    - Backend dependencies check the authenticated user's role before allowing protected actions. Owner, Admin, Recruiter, and Job Seeker APIs are separated.

14. Can a Job Seeker access Admin APIs?
    - No. Admin and Owner routes require Admin or Owner roles, so Job Seeker and Recruiter accounts are blocked.

15. Can a Recruiter update another recruiter's job?
    - No. Recruiter job update queries filter by both job ID and current recruiter ID.

16. How are fake jobs prevented?
    - Active public jobs require an active recruiter account, verified recruiter profile, linked company, verified company, active job status, valid deadline, and active moderation status.

17. How does company verification work?
    - New companies start as pending. Owner/Admin users can verify or reject them. Verified companies get a blue tick and trusted status.

18. How does recruiter verification work?
    - Recruiter profiles start as pending under a company. Owner/Admin users can verify or reject them. Only verified recruiters under verified companies can publish active public jobs.

19. What is the blue tick?
    - It is a visual indicator that a company or recruiter has been verified by Owner/Admin.

20. How does the swipe system work?
    - Job seekers see one job at a time. LIKE applies, REJECT skips, SAVE stores the job, and undo can reverse the latest swipe.

21. Is match score machine learning?
    - No. Match score is rule-based weighted scoring, not machine learning.

22. Why use rule-based match score?
    - It is explainable, predictable, easier to test, and suitable for a final year project without needing a training dataset.

23. What fields affect match score?
    - Skills, experience level, preferred job type, location, and work mode.

24. How is duplicate application prevented?
    - The backend checks whether the job seeker already applied to the job and the database also has a unique constraint on job seeker and job.

25. How is file upload secured?
    - Uploads validate file extension, MIME type, and size. Stored filenames use UUIDs, dangerous extensions are rejected, and uploads stay under `backend/uploads`.

26. What upload limits are used?
    - Resume PDFs allow only PDF up to 5 MB. Profile images and company logos allow JPG, JPEG, PNG, and WEBP up to 2 MB.

27. How is password reset secured?
    - The reset token is not returned in API responses. New reset tokens are stored as hashes, and development-only demo tokens can be checked from backend console output.

28. Why does forgot password return a generic message?
    - It avoids revealing whether an email account exists.

29. How is chat controlled?
    - Chat can only be started by the recruiter after shortlisting an application. Only the recruiter, job seeker, and moderators can access the thread.

30. Can a job seeker start chat?
    - No. Job seekers can reply only after the recruiter starts the conversation.

31. How do reports work?
    - Job seekers can report jobs or recruiters. Owner/Admin users review reports and can update report status or moderate related content.

32. What are notifications used for?
    - Notifications inform users about application status changes, chat events, reports, verification updates, and moderation actions.

33. What is the application timeline?
    - It records important application events such as applied, viewed, shortlisted, withdrawn, chat started, and admin moderation actions.

34. What is the Owner role?
    - Owner is the highest role. Owner can create and manage Admin accounts and access moderation tools.

35. What is the Admin role?
    - Admin can moderate normal users, jobs, applications, reports, companies, recruiters, reviews, and chats, but cannot manage other admins.

36. How are company reviews controlled?
    - Only Job Seekers who applied to a job from that company can review it, and each job seeker can review a company only once.

37. How is average rating updated?
    - The backend recalculates the company's visible review average when reviews are created, hidden, or shown.

38. What security improvements were added?
    - Password reset token hiding, upload validation, route authorization audit, rate limiting, CORS production safety, strong JWT checks, and safer error messages.

39. What are the current limitations?
    - Email sending is local/demo only, uploads use local storage, rate limiting is in-memory, and matching is rule-based.

40. What is the future scope?
    - SMTP email, cloud file storage, Redis-backed rate limiting, automated company verification, advanced recommendation, analytics, and exportable admin reports.

41. Does the platform support undergraduate students?
    - Yes. Job seekers can select Undergraduate or Graduate. Undergraduate users can add current year, joining year, expected graduation year, CGPA, stream, internship preference, marksheets, and certificates.

42. How are academic documents protected?
    - Documents are not public. Job seekers can access their own documents, recruiters can view only documents of candidates who applied to their jobs, and Owner/Admin users can access them for moderation or support.

43. How does the academic profile help recruiters?
    - Recruiters can filter candidates by academic status, stream, graduation year, CGPA, skills, and certificates, which helps separate internship-ready undergraduate candidates from graduate full-time candidates.
