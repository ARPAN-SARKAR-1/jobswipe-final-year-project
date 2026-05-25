# Testing Checklist

Use the `Status` column during manual testing. Suggested values: `Pending`, `Pass`, `Fail`, or `Blocked`.

| Test Case ID | Feature | Steps | Expected Result | Status |
|---|---|---|---|---|
| AUTH-01 | Owner login | Select Owner on login page and login with Owner demo credentials. | Owner reaches Admin Dashboard with Owner controls. | Pending |
| AUTH-02 | Admin login | Select Admin and login with Admin demo credentials. | Admin reaches Admin Dashboard without Owner-only admin management rights. | Pending |
| AUTH-03 | Recruiter login | Select Recruiter and login with Recruiter demo credentials. | Recruiter reaches Recruiter Dashboard. | Pending |
| AUTH-04 | Job Seeker login | Select Job Seeker and login with Job Seeker demo credentials. | Job Seeker reaches Job Seeker Dashboard. | Pending |
| AUTH-05 | Wrong role login | Select Recruiter while using Job Seeker credentials. | Login fails with a safe role/credential message. | Pending |
| AUTH-06 | Public signup allowed roles | Create account as Job Seeker and Recruiter. | Signup succeeds for Job Seeker and Recruiter roles. | Pending |
| AUTH-07 | Public signup blocked roles | Try to send Admin or Owner role in signup request. | Backend rejects Admin and Owner public signup. | Pending |
| AUTH-08 | Logout | Login, then logout. | Token and stored user are cleared. | Pending |
| AUTH-09 | Login rate limit | Send repeated failed login attempts for same email/IP. | Backend returns 429 after limit is reached. | Pending |
| AUTH-10 | Revoked token access | Login, call logout, then use the same token on `/api/auth/me`. | Backend returns 401 for the revoked token. | Pending |
| AUTH-11 | Access token expiry | Decode a newly issued JWT or inspect backend setting. | Token expiry is 30 minutes by default. | Pending |
| CAPTCHA-01 | CAPTCHA challenge | Call `GET /api/security/captcha`. | Response contains `captcha_id` and a math question. | Pending |
| CAPTCHA-02 | Login missing CAPTCHA | Submit login without CAPTCHA while login CAPTCHA is enabled. | Backend rejects with CAPTCHA error. | Pending |
| CAPTCHA-03 | Login wrong CAPTCHA | Submit login with an incorrect CAPTCHA answer. | Backend rejects with CAPTCHA verification failed. | Pending |
| CAPTCHA-04 | Login correct CAPTCHA | Submit login with valid role, credentials, and CAPTCHA. | Login succeeds for Owner, Admin, Recruiter, and Job Seeker roles. | Pending |
| CAPTCHA-05 | CAPTCHA single-use | Reuse the same CAPTCHA on a second request. | Backend rejects the reused CAPTCHA. | Pending |
| CAPTCHA-06 | Expired CAPTCHA | Submit a CAPTCHA after expiry or with forced expired test data. | Backend returns expired CAPTCHA message. | Pending |
| CAPTCHA-07 | Signup CAPTCHA | Submit signup with and without valid CAPTCHA. | Signup requires valid CAPTCHA when enabled. | Pending |
| CAPTCHA-08 | Forgot/reset CAPTCHA | Submit forgot/reset password with and without valid CAPTCHA. | Backend requires valid CAPTCHA when enabled. | Pending |
| CAPTCHA-09 | Admin CAPTCHA settings | Owner/Admin disables and re-enables CAPTCHA settings. | Backend respects the setting and dashboard toggle updates. | Pending |
| RESET-01 | Forgot password response | Call forgot password API. | Response contains generic message and no reset token. | Pending |
| RESET-02 | Reset password | Use valid reset token from backend development console or test setup. | Password reset succeeds and token cannot be reused. | Pending |
| RESET-03 | Forgot password rate limit | Send repeated forgot password requests for same email/IP. | Backend returns 429 after limit is reached. | Pending |
| UPLOAD-01 | Resume upload valid | Upload a PDF resume below 5 MB. | Upload succeeds and resume URL is saved. | Pending |
| UPLOAD-02 | Resume upload invalid | Upload `.exe`, `.html`, `.js`, or non-PDF file as resume. | Upload is rejected with invalid file type. | Pending |
| UPLOAD-03 | Resume upload oversized | Upload PDF above 5 MB. | Upload is rejected with size error. | Pending |
| UPLOAD-04 | Profile image valid | Upload JPG, JPEG, PNG, or WEBP below 2 MB. | Upload succeeds and image renders. | Pending |
| UPLOAD-05 | Profile image invalid | Upload script, archive, or unsupported image type. | Upload is rejected with invalid file type. | Pending |
| UPLOAD-06 | Company logo valid | Upload JPG, JPEG, PNG, or WEBP below 2 MB. | Upload succeeds and logo renders. | Pending |
| UPLOAD-07 | Company logo invalid | Upload unsupported company logo type. | Upload is rejected with invalid file type. | Pending |
| FILE-01 | Resume public URL blocked | Open `/uploads/resumes/{filename}` without auth. | Resume is not publicly served. | Pending |
| FILE-02 | Own resume access | Job seeker opens own resume through `/api/files/resumes/{filename}` with token. | Resume opens successfully. | Pending |
| FILE-03 | Recruiter applicant resume access | Recruiter opens resume for an applicant to their own job. | Resume opens successfully. | Pending |
| FILE-04 | Recruiter cross-access blocked | Recruiter A opens resume for applicant to Recruiter B's job only. | Backend returns 403 or 404. | Pending |
| FILE-05 | Job seeker cross-access blocked | Job seeker A opens Job seeker B's resume. | Backend returns 403 or 404. | Pending |
| ROLE-01 | Admin API blocked for Job Seeker | Call admin users API with Job Seeker token. | Backend returns 403. | Pending |
| ROLE-02 | Admin API blocked for Recruiter | Call admin users API with Recruiter token. | Backend returns 403. | Pending |
| ROLE-03 | Recruiter API blocked for Job Seeker | Call recruiter applications API with Job Seeker token. | Backend returns 403. | Pending |
| ROLE-04 | Recruiter ownership | Recruiter tries to update another recruiter's job. | Backend returns 404 or 403. | Pending |
| ROLE-05 | Application ownership | Job seeker tries to withdraw another user's application. | Backend blocks access. | Pending |
| ROLE-06 | Recruiter application isolation | Recruiter A requests or updates Recruiter B's application. | Backend returns 404 or 403. | Pending |
| ROLE-07 | Job seeker timeline isolation | Job seeker A opens Job seeker B's application timeline. | Backend returns 403 or 404. | Pending |
| COMPANY-01 | Company profile save | Recruiter updates company profile. | Profile saves and starts as pending if new. | Pending |
| COMPANY-02 | Company verification | Owner/Admin verifies company. | Company status becomes verified and blue tick appears. | Pending |
| COMPANY-03 | Company rejection | Owner/Admin rejects company. | Company status becomes rejected and public job posting is blocked. | Pending |
| COMPANY-04 | Recruiter verification | Owner/Admin verifies recruiter. | Recruiter status becomes verified and trusted badge can appear. | Pending |
| COMPANY-05 | Unverified posting block | Pending recruiter or company tries to post active job. | Backend returns 403 with clear message. | Pending |
| COMPANY-06 | Verified posting allowed | Verified recruiter under verified company posts active job. | Job is created and linked to verified company. | Pending |
| JOB-01 | Fake company prevention | Recruiter sends fake company name in job post request. | Backend uses linked verified company instead. | Pending |
| JOB-02 | Job deadline validation | Recruiter submits past deadline. | Backend rejects the request. | Pending |
| JOB-03 | Bond details | Recruiter posts job with bond details. | Bond years and details appear on job UI. | Pending |
| JOB-04 | Required skills | Recruiter selects duplicate skills. | Backend stores de-duplicated skills. | Pending |
| SEEKER-01 | Profile update | Job seeker updates education, skills, preferences, GitHub. | Profile saves and dashboard completion updates. | Pending |
| SEEKER-02 | Swipe apply | Job seeker swipes right on verified job. | Application is created. | Pending |
| SEEKER-03 | Swipe save | Job seeker saves a job. | Job appears in saved jobs. | Pending |
| SEEKER-04 | Swipe reject | Job seeker rejects a job. | Job is skipped from current feed. | Pending |
| SEEKER-05 | Undo swipe | Job seeker uses undo after swipe. | Latest swipe is removed. | Pending |
| APP-01 | Apply | Job seeker applies from job details or list. | Application is created with status applied. | Pending |
| APP-02 | Duplicate application | Job seeker applies to same job again. | Backend returns conflict and duplicate is blocked. | Pending |
| APP-03 | Withdraw | Job seeker withdraws own applied application. | Status becomes withdrawn. | Pending |
| APP-04 | Timeline | Open application timeline. | Timeline shows application events. | Pending |
| REC-01 | Recruiter applications | Recruiter opens received applications. | Only own job applications appear. | Pending |
| REC-02 | Recruiter status update | Recruiter marks application viewed, shortlisted, or rejected. | Status updates and notification/timeline event is created. | Pending |
| REC-03 | Withdrawn update block | Recruiter tries to update withdrawn application. | Backend rejects the update. | Pending |
| CHAT-01 | Job seeker start blocked | Job seeker tries to start chat. | Backend returns 403. | Pending |
| CHAT-02 | Recruiter start before shortlist | Recruiter starts chat before shortlisting. | Backend rejects chat start. | Pending |
| CHAT-02A | Recruiter start after viewed | Recruiter marks application viewed, then starts chat. | Backend rejects chat start until shortlisted. | Pending |
| CHAT-03 | Recruiter start after shortlist | Recruiter shortlists and starts chat. | Chat thread is created. | Pending |
| CHAT-04 | Participant messages | Recruiter and job seeker send messages after chat starts. | Messages are saved and visible to participants. | Pending |
| CHAT-05 | Chat rate limit | Send rapid repeated chat messages. | Backend returns 429 after limit is reached. | Pending |
| CHAT-06 | Cross-recruiter chat blocked | Recruiter A starts or reads chat for Recruiter B's job application. | Backend returns 403 or 404. | Pending |
| CHAT-07 | Withdrawn/rejected chat blocked | Recruiter starts chat after application is withdrawn or rejected. | Backend rejects chat start. | Pending |
| REPORT-01 | Report job | Job seeker reports a job. | Report is created and admins are notified. | Pending |
| REPORT-02 | Report recruiter | Job seeker reports a recruiter. | Report is created and admins are notified. | Pending |
| REPORT-03 | Report moderation | Owner/Admin updates report status. | Status changes and user notification is created. | Pending |
| REPORT-04 | Report rate limit | Send repeated reports from same user. | Backend returns 429 after limit is reached. | Pending |
| ADMIN-01 | Dashboard | Owner/Admin opens dashboard. | Summary cards and moderation tables load. | Pending |
| ADMIN-02 | Owner creates admin | Owner creates new admin. | Admin account is created. | Pending |
| ADMIN-03 | Admin cannot manage admins | Admin tries to suspend another admin. | Backend returns 403. | Pending |
| ADMIN-04 | User suspension | Owner/Admin suspends normal user. | User status becomes suspended. | Pending |
| ADMIN-05 | Job moderation | Owner/Admin pauses, activates, or removes job. | Job moderation status updates. | Pending |
| ADMIN-06 | Application moderation | Owner/Admin pauses or activates application. | Application admin status updates. | Pending |
| ADMIN-07 | Chat moderation | Owner/Admin pauses or activates chat thread. | Chat status updates. | Pending |
| USER-RISK-01 | New job seeker risk | Create a job seeker with incomplete profile. | Rule-based user risk assessment is generated as low/medium. | Pending |
| USER-RISK-02 | Unverified recruiter risk | Create recruiter with unverified company. | User risk reasons mention unverified recruiter/company state. | Pending |
| USER-RISK-03 | Reported recruiter risk | Report a recruiter. | Recruiter user risk score increases and appears in Admin dashboard if medium or above. | Pending |
| USER-RISK-04 | Suspicious user queue | Open Admin Dashboard after risk generation. | Suspicious Users section shows flagged users with risk score/reasons. | Pending |
| USER-RISK-05 | User risk review/suspend | Owner/Admin reviews and suspends a suspicious user. | Risk item is marked reviewed and user account is suspended. | Pending |
| REVIEW-01 | Review eligibility | Job seeker reviews company after applying to a job from that company. | Review is created. | Pending |
| REVIEW-02 | Review ineligible | Job seeker reviews company without applying. | Backend returns 403. | Pending |
| REVIEW-03 | Duplicate review | Job seeker reviews same company twice. | Backend returns conflict. | Pending |
| REVIEW-04 | Rating average | Create, hide, and show review. | Average rating and total visible reviews update. | Pending |
| REVIEW-05 | Review moderation | Owner/Admin hides and shows review. | Public company page respects visibility. | Pending |
| REVIEW-06 | Recruiter review eligible | Job seeker reviews recruiter after applying to that recruiter's job or after chat. | Review is created and recruiter rating updates. | Pending |
| REVIEW-07 | Recruiter review ineligible | Job seeker reviews unrelated recruiter. | Backend returns 403. | Pending |
| REVIEW-08 | Duplicate recruiter review | Job seeker reviews same recruiter twice. | Backend returns conflict. | Pending |
| REVIEW-09 | Recruiter cannot manage reviews | Recruiter tries to call admin review moderation APIs. | Backend returns 403. | Pending |
| REVIEW-10 | Review analytics | Owner/Admin opens review analytics. | Highest/lowest companies, low-rated recruiters, and flagged/hidden counts load. | Pending |
| REVIEW-11 | Review anonymity | Job seeker submits anonymous review. | Public page hides reviewer name; Admin moderation still shows reviewer. | Pending |
| NOTIF-01 | Notification list | User opens notifications page. | Notifications load. | Pending |
| NOTIF-02 | Mark read | User marks notifications read. | Unread count updates. | Pending |
| PRIVACY-01 | Terms page | Open `/terms`. | Terms page loads. | Pending |
| PRIVACY-02 | Privacy page | Open `/privacy`. | Privacy page loads and resume visibility explanation is present. | Pending |
| DOCS-01 | API docs | Run backend and open `/docs`. | Swagger documentation loads. | Pending |
| DOCS-02 | Production API docs disabled | Start app with `ENV=production` and open `/docs`. | Swagger/OpenAPI routes are disabled. | Pending |
| BUILD-01 | Backend compile | Run `python -m compileall app`. | Compile succeeds. | Pending |
| BUILD-02 | Alembic | Run `alembic upgrade head`. | Database reaches migration head. | Pending |
| BUILD-03 | Frontend build | Run `npm.cmd run build`. | Next.js production build succeeds. | Pending |
