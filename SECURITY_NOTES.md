# Security Notes

## Authentication And Passwords

- User passwords are hashed with bcrypt through passlib before storage.
- JWT authentication is used for logged-in API access.
- Access tokens expire after 30 minutes by default.
- JWTs include a `jti` identifier so logout can revoke the current token.
- Logout uses an in-memory token denylist for local/demo use until server restart.
- Production deployments should use a Redis-backed token revocation store.
- Production startup requires a strong `JWT_SECRET`; weak demo values such as `change_this_secret` are rejected when `ENV=production`.
- Role-based access control separates Owner, Admin, Recruiter, and Job Seeker permissions.
- BOLA/IDOR protection is enforced by combining role checks with ownership filters in resource queries.
- Owner/Admin moderation routes are protected from normal users.
- Public signup allows only Job Seeker and Recruiter accounts.
- Swagger/OpenAPI docs are disabled when `ENV=production`.

## CAPTCHA And Login Audit

- Login, signup, forgot password, and reset password can require an internal math CAPTCHA for local/demo protection.
- CAPTCHA answers are stored only as hashes, expire after 5 minutes, and are single-use.
- Owner/Admin users can enable or disable CAPTCHA requirements from Security Settings.
- The internal CAPTCHA is designed for final year demo use. Production deployments should replace or extend it with Google reCAPTCHA, hCaptcha, Cloudflare Turnstile, or another managed provider.
- Failed login attempts are recorded with email, selected role, IP address, success flag, and internal failure reason for audit and risk scoring.
- Login responses use safe generic messages and do not expose whether the email, password, or selected role was the exact failure.

## Password Reset

- Password reset tokens are not returned in API responses.
- Reset tokens are stored as a server-side hash for new reset requests.
- In development mode, the backend may log the raw reset token at debug level for local demo testing.
- In production mode, reset tokens are not printed.
- Email delivery is future scope; the current local flow is designed for development and review demos without exposing tokens to the frontend.

## File Uploads

- Resume uploads allow only PDF files up to 5 MB.
- Profile picture uploads allow only JPG, JPEG, PNG, and WEBP files up to 2 MB.
- Company logo uploads allow only JPG, JPEG, PNG, and WEBP files up to 2 MB.
- Upload validation checks both MIME type and file extension.
- Uploaded files are stored with UUID-based filenames instead of trusting the original filename.
- Upload paths are constrained to `backend/uploads`, which is excluded from Git.
- Dangerous executable or script extensions are rejected.
- Resume PDFs are not served through the public static uploads route.
- Resume access goes through `GET /api/files/resumes/{filename}` with role and ownership checks.
- Job seekers can access their own resume, recruiters can access resumes only for applicants to their own jobs, and Owner/Admin users can access resumes for moderation.
- Academic documents such as marksheets and certificates are not public and are served through `GET /api/files/jobseeker-documents/{filename}` with the same ownership-based access rules.
- Recruiters cannot access documents of candidates who did not apply to their jobs.
- Academic document uploads validate file extension, MIME type, file signature, and size before saving with UUID filenames.
- If `python-magic` is available, upload validation can use it for MIME detection; otherwise the backend uses extension, declared MIME type, and basic file-signature checks.

## Rate Limiting And CORS

- Login is limited to 5 attempts per email/IP per 10 minutes.
- Forgot password is limited to 3 attempts per email/IP per 15 minutes.
- Reset password has a small token/IP limit to reduce brute-force attempts.
- Job and recruiter reports are limited to 5 reports per user per hour.
- Chat messages are limited to 20 messages per user per minute.
- The current in-memory limiter is suitable for local demos and single-process review environments.
- Redis-backed rate limiting is future scope for production deployments with multiple backend instances.
- CORS origins come from `FRONTEND_URL`.
- Wildcard CORS origins are not allowed when `ENV=production`.

## Data Visibility

- Resumes are not public.
- Academic documents are not public.
- A recruiter can see a resume, marksheet, or certificate only after the job seeker applies to that recruiter's job.
- Owner/Admin users may access records only for moderation or support workflows.

## Fake Job Prevention

- Recruiter/company verification helps prevent fake companies and fake jobs.
- Public job posting requires an active recruiter account, verified recruiter profile, verified company, verified company membership, and active moderation status.
- Job seeker feeds show only active public jobs from verified companies and verified recruiters.
- Company claim verification prevents recruiters from freely using verified or famous company names without approval.
- Official-domain claim checks require the company email domain to match the requested company domain.
- Reserved brand names such as TCS, Infosys, Wipro, Accenture, and similar variants are marked high risk for Owner/Admin review.
- Company-level roles separate `COMPANY_OWNER`, `COMPANY_ADMIN`, and `COMPANY_RECRUITER` permissions from global platform roles.
- Fake job alerts use a rule-based risk scoring engine for money requests, suspicious domains, unverified company/recruiter state, reports, duplicate spam, and unrealistic salary signals.
- Critical jobs are auto-paused for admin review; high-risk jobs are flagged and kept out of public feeds through moderation.
- Candidate alerts use rule-based scoring for recruiter reports, missing profile details, suspicious links, repeated applications, and duplicate contact signals.
- Suspicious user alerts use a rule-based user risk scoring engine for incomplete profiles, failed login attempts, suspicious links, repeated reports, unverified recruiter/company state, risky jobs, and rejected company claims.
- Risk scoring is rule-based and ML-ready, but it is not a full trained machine learning system.
- Chat is backend-gated by the `SHORTLISTED` application status and recruiter ownership of the job.
- Chat is blocked for applied, viewed, rejected, withdrawn, admin-paused applications, paused/removed jobs, and suspended users.

## Matching And Duplicate Safety

- Match score is rule-based weighted scoring using profile and job fields. It is not a machine learning model.
- Duplicate applications are blocked by backend application checks.
- Duplicate company reviews are blocked by backend eligibility checks.
- Company reviews require the job seeker to have a shortlisted-or-later application for a job from that company.
- Recruiter reviews require the job seeker to have a shortlisted-or-later application for one of the recruiter's jobs; a recruiter-started chat after shortlisting also confirms the same relationship.
- Anonymous reviews hide the job seeker name publicly, but Owner/Admin users can still see reviewer identity for moderation and safety.
- Owner/Admin users can hide, show, or flag abusive company and recruiter reviews.
- Hidden reviews are excluded from public review lists and rating rollups.

## Future Scope

- Production email service for password reset delivery.
- Production SMTP service for company claim verification emails.
- Production CAPTCHA provider integration.
- Official company document verification for high-risk brand claims.
- Cloud storage with signed upload/download URLs.
- Redis-backed rate limiting.
- Malware scanning for uploaded files.
- Automated company verification.
- Advanced machine-learning-based recommendation.
- Trained ML model for fake-user detection.
- Audit dashboards for security-sensitive admin actions.
