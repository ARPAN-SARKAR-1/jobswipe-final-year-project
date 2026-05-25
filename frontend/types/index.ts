export type Role = "JOB_SEEKER" | "RECRUITER" | "ADMIN" | "OWNER";
export type AcademicStatus = "UNDERGRADUATE" | "GRADUATE";
export type JobSeekerDocumentType = "RESUME" | "MARKSHEET" | "CERTIFICATE" | "INTERNSHIP_CERTIFICATE" | "COURSE_CERTIFICATE" | "OTHER";

export type User = {
  id: number;
  name: string;
  email: string;
  role: Role;
  profile_picture_url?: string | null;
  accepted_terms: boolean;
  accepted_terms_at?: string | null;
  accepted_privacy: boolean;
  accepted_privacy_at?: string | null;
  account_status: "ACTIVE" | "SUSPENDED";
  suspension_reason?: string | null;
  is_protected_owner: boolean;
  created_at: string;
};

export type Job = {
  id: number;
  recruiter_id: number;
  company_id?: number | null;
  title: string;
  company_name: string;
  company_logo_url?: string | null;
  location: string;
  job_type: string;
  work_mode: string;
  salary?: string | null;
  required_skills: string;
  required_skills_list?: string[];
  match_score?: number | null;
  matched_skills?: string[];
  missing_skills?: string[];
  match_note?: string | null;
  existing_application_status?: Application["status"] | null;
  required_experience_level: string;
  description: string;
  eligibility?: string | null;
  deadline: string;
  is_active: boolean;
  has_bond: boolean;
  bond_years?: number | null;
  bond_details?: string | null;
  moderation_status: "ACTIVE" | "PAUSED" | "REMOVED";
  moderation_reason?: string | null;
  company_verification_status?: VerificationStatus | null;
  recruiter_verification_status?: VerificationStatus | null;
  company_average_rating?: number | null;
  company_total_reviews?: number | null;
  trusted_job: boolean;
  eligible_academic_status: "UNDERGRADUATE" | "GRADUATE" | "BOTH";
  eligible_streams?: string | null;
  minimum_cgpa?: number | null;
  eligible_graduation_years?: string | null;
  internship_available: boolean;
  created_at: string;
  updated_at: string;
};

export type JobSeekerProfile = {
  id: number;
  user_id: number;
  name: string;
  email: string;
  profile_picture_url?: string | null;
  resume_pdf_url?: string | null;
  phone?: string | null;
  github_url?: string | null;
  education?: string | null;
  degree?: string | null;
  college?: string | null;
  passing_year?: number | null;
  cgpa_or_percentage?: string | null;
  skills?: string | null;
  skills_list?: string[];
  experience_level?: string | null;
  preferred_location?: string | null;
  preferred_job_type?: string | null;
  academic_status?: AcademicStatus | null;
  degree_name?: string | null;
  stream_or_branch?: string | null;
  college_or_university?: string | null;
  admission_year?: number | null;
  expected_graduation_year?: number | null;
  current_year?: "1st Year" | "2nd Year" | "3rd Year" | "4th Year" | "Final Year" | null;
  current_semester?: string | null;
  current_cgpa?: number | null;
  internship_preference?: "Internship" | "Training" | "Part-time" | "Remote Internship" | "Full-time after graduation" | null;
  preferred_internship_duration?: string | null;
  available_from?: string | null;
  open_to_remote: boolean;
  open_to_relocation: boolean;
  final_cgpa_or_percentage?: string | null;
  looking_for?: "Full-time" | "Internship" | "Contract" | "Remote" | "Hybrid" | null;
  created_at: string;
  updated_at: string;
};

export type JobSeekerDocument = {
  id: number;
  job_seeker_id: number;
  document_type: JobSeekerDocumentType;
  title: string;
  file_url: string;
  original_filename: string;
  stored_filename: string;
  mime_type: string;
  file_size: number;
  is_verified: boolean;
  related_skill?: string | null;
  issuing_organization?: string | null;
  issue_date?: string | null;
  credential_url?: string | null;
  uploaded_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyProfile = {
  id: number;
  recruiter_id: number;
  company_id?: number | null;
  company_name?: string | null;
  company_logo_url?: string | null;
  company_type?: CompanyType | null;
  industry?: string | null;
  website?: string | null;
  official_email_domain?: string | null;
  description?: string | null;
  headquarters_location?: string | null;
  location?: string | null;
  founded_year?: number | null;
  company_size?: string | null;
  registration_number?: string | null;
  verification_status: VerificationStatus;
  company_verification_note?: string | null;
  company_verified_at?: string | null;
  company_verified_by_admin_id?: number | null;
  average_rating: number;
  total_reviews: number;
  designation?: string | null;
  department?: string | null;
  official_email?: string | null;
  recruiter_verification_status: VerificationStatus;
  verification_note?: string | null;
  verified_at?: string | null;
  verified_by_admin_id?: number | null;
  created_at: string;
  updated_at: string;
};

export type AdminRecruiterVerification = CompanyProfile & {
  recruiter_name: string;
  recruiter_email: string;
  account_status: "ACTIVE" | "SUSPENDED";
};

export type VerificationStatus = "PENDING" | "VERIFIED" | "REJECTED";
export type CompanyRole = "COMPANY_OWNER" | "COMPANY_ADMIN" | "COMPANY_RECRUITER";
export type ClaimStatus = "PENDING" | "VERIFIED" | "REJECTED" | "EXPIRED";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type RiskAutoAction = "NONE" | "FLAGGED" | "PAUSED";

export type CompanyType = "MNC" | "Startup" | "Product-based" | "Service-based" | "Consultancy" | "Government" | "Non-profit" | "Other";

export type Company = {
  id: number;
  company_name: string;
  company_logo_url?: string | null;
  company_type: CompanyType;
  industry?: string | null;
  website?: string | null;
  official_email_domain?: string | null;
  description?: string | null;
  headquarters_location?: string | null;
  founded_year?: number | null;
  company_size?: string | null;
  registration_number?: string | null;
  verification_status: VerificationStatus;
  verification_note?: string | null;
  verified_by_admin_id?: number | null;
  verified_at?: string | null;
  average_rating: number;
  total_reviews: number;
  active_jobs_count: number;
  recruiter_count: number;
  created_at: string;
  updated_at: string;
};

export type CompanyRecruiter = {
  id: number;
  user_id: number;
  recruiter_name: string;
  recruiter_email: string;
  designation?: string | null;
  department?: string | null;
  official_email?: string | null;
  recruiter_verification_status: VerificationStatus;
  account_status: "ACTIVE" | "SUSPENDED";
  verified_at?: string | null;
  average_rating: number;
  total_reviews: number;
};

export type CompanyDetail = Company & {
  recruiters: CompanyRecruiter[];
  active_jobs: Job[];
};

export type CompanyReview = {
  id: number;
  company_id: number;
  job_seeker_id: number;
  application_id?: number | null;
  rating: number;
  overall_rating: number;
  work_culture_rating: number;
  interview_process_rating: number;
  salary_transparency_rating: number;
  growth_opportunity_rating: number;
  review_title?: string | null;
  review_text?: string | null;
  pros?: string | null;
  cons?: string | null;
  is_anonymous: boolean;
  is_visible: boolean;
  moderation_status: "VISIBLE" | "HIDDEN" | "FLAGGED";
  reviewer_name?: string | null;
  reviewer_email?: string | null;
  company_name?: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyReviewSummary = {
  company_id: number;
  average_overall_rating: number;
  work_culture_average: number;
  interview_process_average: number;
  salary_transparency_average: number;
  growth_opportunity_average: number;
  total_reviews: number;
  flagged_reviews: number;
  hidden_reviews: number;
  top_positive_keywords: string[];
  top_negative_keywords: string[];
};

export type RecruiterPublicProfile = {
  id: number;
  name: string;
  company_id?: number | null;
  company_name?: string | null;
  company_logo_url?: string | null;
  company_verification_status?: VerificationStatus | null;
  designation?: string | null;
  department?: string | null;
  recruiter_verification_status: VerificationStatus;
  average_rating: number;
  total_reviews: number;
  active_jobs_count: number;
  created_at: string;
};

export type RecruiterReview = {
  id: number;
  recruiter_id: number;
  job_seeker_id: number;
  application_id?: number | null;
  overall_rating: number;
  communication_rating: number;
  response_time_rating: number;
  professionalism_rating: number;
  transparency_rating: number;
  review_title?: string | null;
  review_text?: string | null;
  is_anonymous: boolean;
  is_visible: boolean;
  moderation_status: "VISIBLE" | "HIDDEN" | "FLAGGED";
  reviewer_name?: string | null;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
  company_name?: string | null;
  created_at: string;
  updated_at: string;
};

export type RecruiterReviewSummary = {
  recruiter_id: number;
  average_overall_rating: number;
  communication_average: number;
  response_time_average: number;
  professionalism_average: number;
  transparency_average: number;
  total_reviews: number;
  flagged_reviews: number;
  hidden_reviews: number;
  top_feedback_keywords: string[];
};

export type ReviewAnalytics = {
  highest_rated_companies: Record<string, unknown>[];
  lowest_rated_companies: Record<string, unknown>[];
  most_reviewed_companies: Record<string, unknown>[];
  low_rated_recruiters: Record<string, unknown>[];
  recent_company_reviews: Record<string, unknown>[];
  recent_recruiter_reviews: Record<string, unknown>[];
  hidden_reviews_count: number;
  flagged_reviews_count: number;
};

export type CompanyClaim = {
  id: number;
  company_id?: number | null;
  requested_company_name: string;
  requested_domain: string;
  requester_user_id: number;
  official_email: string;
  claim_status: ClaimStatus;
  email_verified_at?: string | null;
  reviewed_by_admin_id?: number | null;
  admin_note?: string | null;
  risk_score: number;
  risk_level: RiskLevel;
  requires_admin_review: boolean;
  risk_reasons?: string | null;
  company_name?: string | null;
  requester_name?: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyMember = {
  id: number;
  company_id: number;
  user_id: number;
  company_role: CompanyRole;
  verification_status: VerificationStatus;
  requested_at?: string | null;
  verified_at?: string | null;
  verified_by_user_id?: number | null;
  note?: string | null;
  user_name?: string | null;
  user_email?: string | null;
  company_name?: string | null;
  created_at: string;
  updated_at: string;
};

export type JobRiskAssessment = {
  id: number;
  job_id: number;
  risk_score: number;
  risk_level: RiskLevel;
  reasons?: string | null;
  auto_action: RiskAutoAction;
  reviewed_by_admin_id?: number | null;
  reviewed_at?: string | null;
  job_title?: string | null;
  company_name?: string | null;
  recruiter_id?: number | null;
  recruiter_name?: string | null;
  moderation_status?: Job["moderation_status"] | null;
  created_at: string;
  updated_at: string;
};

export type CandidateRiskAssessment = {
  id: number;
  job_seeker_id: number;
  risk_score: number;
  risk_level: RiskLevel;
  reasons?: string | null;
  reviewed_by_admin_id?: number | null;
  reviewed_at?: string | null;
  admin_note?: string | null;
  job_seeker_name?: string | null;
  job_seeker_email?: string | null;
  created_at: string;
  updated_at: string;
};

export type UserRiskAssessment = {
  id: number;
  user_id: number;
  risk_score: number;
  risk_level: RiskLevel;
  reasons?: string | null;
  last_evaluated_at?: string | null;
  reviewed_by_admin_id?: number | null;
  reviewed_at?: string | null;
  admin_note?: string | null;
  user_name?: string | null;
  user_email?: string | null;
  user_role?: Role | null;
  account_status?: User["account_status"] | null;
  created_at: string;
  updated_at: string;
};

export type SecuritySettings = {
  id: number;
  captcha_login_enabled: boolean;
  captcha_signup_enabled: boolean;
  captcha_forgot_password_enabled: boolean;
  captcha_reports_enabled: boolean;
  captcha_company_claims_enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type Swipe = {
  id: number;
  job_seeker_id: number;
  job_id: number;
  action: "LIKE" | "REJECT" | "SAVE";
  created_at: string;
  job?: Job | null;
};

export type Application = {
  id: number;
  job_seeker_id: number;
  job_id: number;
  resume_pdf_url?: string | null;
  github_url?: string | null;
  status: "APPLIED" | "VIEWED" | "SHORTLISTED" | "REJECTED" | "WITHDRAWN";
  admin_status: "ACTIVE" | "PAUSED";
  admin_note?: string | null;
  chat_thread_id?: number | null;
  chat_status?: "ACTIVE" | "CLOSED" | "PAUSED" | null;
  created_at: string;
  updated_at: string;
  job?: Job | null;
  applicant_name?: string;
  applicant_email?: string;
  applicant_github_url?: string | null;
  applicant_resume_pdf_url?: string | null;
  applicant_academic_status?: AcademicStatus | null;
  applicant_degree_name?: string | null;
  applicant_stream_or_branch?: string | null;
  applicant_college_or_university?: string | null;
  applicant_graduation_year?: number | null;
  applicant_current_year?: string | null;
  applicant_cgpa?: number | null;
  applicant_experience_level?: string | null;
  applicant_internship_preference?: string | null;
  applicant_open_to_remote?: boolean;
  applicant_open_to_relocation?: boolean;
  applicant_skills?: string | null;
  applicant_documents?: JobSeekerDocument[];
  job_title?: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type AdminActionLog = {
  id: number;
  admin_id: number;
  action_type: string;
  target_type: string;
  target_id: number;
  reason?: string | null;
  created_at: string;
};

export type Notification = {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  link_url?: string | null;
  created_at: string;
  updated_at: string;
};

export type Report = {
  id: number;
  reporter_id: number;
  job_id?: number | null;
  recruiter_id?: number | null;
  report_type: "FAKE_JOB" | "ASKING_MONEY" | "MISLEADING_INFO" | "ABUSIVE" | "SPAM" | "OTHER";
  description: string;
  status: "PENDING" | "REVIEWED" | "RESOLVED" | "DISMISSED";
  admin_note?: string | null;
  reporter_name?: string | null;
  reporter_email?: string | null;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
  job_title?: string | null;
  created_at: string;
  updated_at: string;
};

export type ApplicationTimelineEvent = {
  id: number;
  application_id: number;
  action: string;
  old_status?: string | null;
  new_status?: string | null;
  note?: string | null;
  created_by_user_id?: number | null;
  created_by_name?: string | null;
  created_at: string;
};

export type ChatThread = {
  id: number;
  application_id: number;
  recruiter_id: number;
  job_seeker_id: number;
  job_id: number;
  status: "ACTIVE" | "CLOSED" | "PAUSED";
  started_by_recruiter: boolean;
  created_at: string;
  updated_at: string;
  job_title?: string | null;
  company_name?: string | null;
  recruiter_name?: string | null;
  job_seeker_name?: string | null;
  application_status?: string | null;
  unread_count: number;
  last_message?: string | null;
  last_message_at?: string | null;
};

export type ChatMessage = {
  id: number;
  thread_id: number;
  sender_id: number;
  sender_name?: string | null;
  sender_role?: Role | null;
  message_text: string;
  is_read: boolean;
  read_at?: string | null;
  deleted_for_sender: boolean;
  deleted_for_receiver: boolean;
  created_at: string;
};
