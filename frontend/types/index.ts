export type Role = "JOB_SEEKER" | "RECRUITER" | "ADMIN" | "OWNER";
export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};
export type CompanyVerificationStatus = "PENDING" | "VERIFIED" | "REJECTED" | "SUSPENDED";
export type RecruiterVerificationStatus = "PENDING" | "VERIFIED" | "REJECTED" | "SUSPENDED";
export type CompanyJoinStatus = "PENDING" | "APPROVED" | "REJECTED";
export type CompanyType = "STARTUP" | "MNC" | "CONSULTANCY" | "AGENCY" | "COLLEGE" | "OTHER";
export type ReviewModerationStatus = "VISIBLE" | "HIDDEN" | "FLAGGED" | "REMOVED";
export type JobSeekerCategory = "UNDERGRADUATE" | "GRADUATE_FRESHER" | "GRADUATE_EXPERIENCED";
export type SectionVisibility = "PRIVATE" | "RECRUITERS_ONLY" | "PUBLIC";
export type StudentVerificationStatus = "STUDENT_UNVERIFIED" | "STUDENT_PENDING" | "STUDENT_VERIFIED" | "STUDENT_REJECTED";
export type GraduationVerificationStatus = "GRADUATION_UNVERIFIED" | "GRADUATION_PENDING" | "GRADUATION_VERIFIED" | "GRADUATION_REJECTED";
export type ExperienceVerificationStatus = "EXPERIENCE_UNVERIFIED" | "EXPERIENCE_PENDING" | "EXPERIENCE_VERIFIED" | "EXPERIENCE_REJECTED";
export type SupportTicketRoleType = "JOB_SEEKER" | "RECRUITER" | "ADMIN_OWNER" | "VISITOR";
export type SupportTicketCategory =
  | "ACCOUNT_LOGIN"
  | "OTP_EMAIL_VERIFICATION"
  | "JOB_APPLICATION"
  | "RECRUITER_COMPANY_VERIFICATION"
  | "PROFILE_DOCUMENT_UPLOAD"
  | "BUG_REPORT"
  | "PRIVACY_DATA_REQUEST"
  | "OTHER";
export type SupportTicketPriority = "LOW" | "MEDIUM" | "HIGH";
export type SupportTicketStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";

export type User = {
  id: number;
  public_user_id?: string | null;
  username?: string | null;
  name: string;
  email: string;
  role: Role;
  profile_picture_url?: string | null;
  bio?: string | null;
  profile_visibility: "PUBLIC" | "PRIVATE";
  accepted_terms: boolean;
  accepted_terms_at?: string | null;
  accepted_privacy: boolean;
  accepted_privacy_at?: string | null;
  email_verified: boolean;
  email_verified_at?: string | null;
  twofa_enabled: boolean;
  account_status: "ACTIVE" | "SUSPENDED";
  suspension_reason?: string | null;
  is_protected_owner: boolean;
  created_at: string;
};

export type Job = {
  id: number;
  job_public_id?: string | null;
  recruiter_id: number;
  company_id?: number | null;
  company_public_id?: string | null;
  company_slug?: string | null;
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
  risk_score: number;
  risk_flags?: string | null;
  company_verified: boolean;
  recruiter_verified: boolean;
  trusted_posting: boolean;
  company_verification_status?: CompanyVerificationStatus | null;
  recruiter_verification_status?: RecruiterVerificationStatus | null;
  created_at: string;
  updated_at: string;
};

export type JobSeekerProfile = {
  id: number;
  user_id: number;
  public_user_id?: string | null;
  username?: string | null;
  name: string;
  email: string;
  profile_picture_url?: string | null;
  resume_pdf_url?: string | null;
  phone?: string | null;
  github_url?: string | null;
  about?: string | null;
  verification_status?: "PENDING" | "VERIFIED" | "REJECTED" | "SUSPENDED";
  certificates_public?: boolean;
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
  job_seeker_category?: JobSeekerCategory | null;
  college_name?: string | null;
  university_name?: string | null;
  course_name?: string | null;
  degree_name?: string | null;
  department_or_branch?: string | null;
  current_year_or_semester?: string | null;
  expected_passing_year?: number | null;
  college_location?: string | null;
  student_id_number?: string | null;
  internship_interest?: boolean;
  preferred_internship_roles?: string | null;
  highest_degree?: string | null;
  graduation_year?: number | null;
  specialization_or_branch?: string | null;
  fresher_skills?: string | null;
  certifications?: string | null;
  project_links?: string | null;
  internship_experience?: string | null;
  preferred_job_roles?: string | null;
  total_experience_years?: number | null;
  current_or_last_company?: string | null;
  current_or_last_role?: string | null;
  employment_type?: string | null;
  notice_period?: string | null;
  previous_companies?: string | null;
  role_history?: string | null;
  key_responsibilities?: string | null;
  tools_technologies?: string | null;
  achievements?: string | null;
  preferred_next_roles?: string | null;
  education_visibility?: SectionVisibility;
  experience_visibility?: SectionVisibility;
  recommendation_visibility?: SectionVisibility;
  reference_visibility?: SectionVisibility;
  certificate_visibility?: SectionVisibility;
  student_verification_status?: StudentVerificationStatus;
  graduation_verification_status?: GraduationVerificationStatus;
  experience_verification_status?: ExperienceVerificationStatus;
  created_at: string;
  updated_at: string;
};

export type CompanyProfile = {
  id: number;
  public_company_id?: string | null;
  slug?: string | null;
  recruiter_id: number;
  name?: string | null;
  company_name?: string | null;
  logo_url?: string | null;
  company_logo_url?: string | null;
  website?: string | null;
  industry?: string | null;
  company_type: CompanyType;
  description?: string | null;
  location?: string | null;
  official_email_domain?: string | null;
  verification_status: CompanyVerificationStatus;
  recruiter_verification_status: RecruiterVerificationStatus;
  company_join_status: CompanyJoinStatus;
  designation?: string | null;
  work_email?: string | null;
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
  membership_id?: number | null;
  member_verification_status: RecruiterVerificationStatus;
  member_join_status: CompanyJoinStatus;
  member_admin_note?: string | null;
};

export type RecruiterCompanyMember = {
  id: number;
  recruiter_id: number;
  company_id: number;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
  company_name?: string | null;
  designation?: string | null;
  work_email?: string | null;
  verification_status: RecruiterVerificationStatus;
  company_join_status: CompanyJoinStatus;
  verified_at?: string | null;
  verified_by_admin_id?: number | null;
  verified_by_company_owner_id?: number | null;
  approved_by_admin_id?: number | null;
  approved_at?: string | null;
  admin_note?: string | null;
  created_at: string;
  updated_at: string;
};

export type UserDocument = {
  id: number;
  owner_user_id: number;
  owner_name?: string | null;
  owner_email?: string | null;
  owner_role?: Role | null;
  document_type: string;
  original_filename?: string | null;
  is_public: boolean;
  visibility: SectionVisibility;
  verification_status: "PENDING" | "VERIFIED" | "REJECTED";
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  review_note?: string | null;
  file_url?: string | null;
  created_at: string;
  updated_at: string;
};

export type PublicDocumentSummary = {
  id: number;
  document_type: string;
  title: string;
  verification_status: "PENDING" | "VERIFIED" | "REJECTED";
  created_at: string;
};

export type PublicCompanySummary = {
  id: number;
  public_company_id?: string | null;
  slug?: string | null;
  name?: string | null;
  logo_url?: string | null;
  designation?: string | null;
  verification_status?: CompanyVerificationStatus | null;
  recruiter_verification_status?: RecruiterVerificationStatus | null;
  recruiter_verified: boolean;
  company_verified: boolean;
};

export type PublicProfile = {
  public_user_id: string;
  username?: string | null;
  name: string;
  role: Role;
  profile_picture_url?: string | null;
  profile_visibility: "PUBLIC" | "PRIVATE";
  is_limited: boolean;
  verified_profile: boolean;
  verification_label?: string | null;
  bio?: string | null;
  skills?: string | null;
  skills_list: string[];
  education?: string | null;
  degree?: string | null;
  college?: string | null;
  experience_level?: string | null;
  preferred_location?: string | null;
  preferred_job_type?: string | null;
  github_url?: string | null;
  job_seeker_verification_status?: "PENDING" | "VERIFIED" | "REJECTED" | "SUSPENDED" | null;
  job_seeker_category?: JobSeekerCategory | null;
  college_name?: string | null;
  university_name?: string | null;
  course_name?: string | null;
  degree_name?: string | null;
  department_or_branch?: string | null;
  current_year_or_semester?: string | null;
  expected_passing_year?: number | null;
  college_location?: string | null;
  internship_interest?: boolean | null;
  preferred_internship_roles?: string | null;
  highest_degree?: string | null;
  graduation_year?: number | null;
  specialization_or_branch?: string | null;
  fresher_skills?: string | null;
  certifications?: string | null;
  project_links?: string | null;
  internship_experience?: string | null;
  preferred_job_roles?: string | null;
  total_experience_years?: number | null;
  current_or_last_company?: string | null;
  current_or_last_role?: string | null;
  employment_type?: string | null;
  notice_period?: string | null;
  previous_companies?: string | null;
  role_history?: string | null;
  key_responsibilities?: string | null;
  tools_technologies?: string | null;
  achievements?: string | null;
  preferred_next_roles?: string | null;
  student_verification_status?: StudentVerificationStatus | null;
  graduation_verification_status?: GraduationVerificationStatus | null;
  experience_verification_status?: ExperienceVerificationStatus | null;
  company?: PublicCompanySummary | null;
  public_documents: PublicDocumentSummary[];
  private_documents: UserDocument[];
  created_at: string;
};

export type CompanyReview = {
  id: number;
  company_id: number;
  reviewer_user_id: number;
  reviewer_name?: string | null;
  application_id?: number | null;
  rating: number;
  title: string;
  review_text: string;
  work_culture_rating?: number | null;
  interview_process_rating?: number | null;
  growth_rating?: number | null;
  is_visible: boolean;
  is_flagged: boolean;
  moderation_status: ReviewModerationStatus;
  created_at: string;
  updated_at: string;
};

export type CompanyPublicProfile = CompanyProfile & {
  average_rating?: number | null;
  review_count: number;
  visible_reviews: CompanyReview[];
  verified_recruiter_count: number;
  verified_recruiters: RecruiterCompanyMember[];
  active_jobs: Job[];
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
  status: "APPLIED" | "VIEWED" | "SHORTLISTED" | "INTERVIEWED" | "HIRED" | "REJECTED" | "WITHDRAWN";
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
  applicant_job_seeker_category?: JobSeekerCategory | null;
  applicant_student_verification_status?: StudentVerificationStatus | null;
  applicant_graduation_verification_status?: GraduationVerificationStatus | null;
  applicant_experience_verification_status?: ExperienceVerificationStatus | null;
  applicant_passing_year?: number | null;
  applicant_total_experience_years?: number | null;
  job_title?: string;
};

export type JobSeekerRecommendation = {
  id: number;
  title: string;
  organization?: string | null;
  issued_by?: string | null;
  issue_date?: string | null;
  file_url?: string | null;
  visibility: SectionVisibility;
  verification_status: "PENDING" | "VERIFIED" | "REJECTED";
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  review_note?: string | null;
  created_at: string;
  updated_at: string;
};

export type JobSeekerReference = {
  id: number;
  reference_name: string;
  reference_role?: string | null;
  organization?: string | null;
  relationship?: string | null;
  email?: string | null;
  phone?: string | null;
  visibility: Exclude<SectionVisibility, "PUBLIC">;
  note?: string | null;
  verification_status: "PENDING" | "VERIFIED" | "REJECTED";
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  review_note?: string | null;
  created_at: string;
  updated_at: string;
};

export type AuthResponse = {
  access_token?: string | null;
  token_type: string;
  user?: User | null;
  requires_email_verification?: boolean;
  requires_2fa?: boolean;
  twofa_recommended?: boolean;
  login_challenge_id?: string | null;
  message: string;
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

export type SupportTicketCreate = {
  name: string;
  email: string;
  role_type: SupportTicketRoleType;
  category: SupportTicketCategory;
  priority: SupportTicketPriority;
  subject: string;
  message: string;
  captcha_challenge_id?: string;
  captcha_answer?: string;
};

export type SupportTicket = {
  id: number;
  ticket_code: string;
  name: string;
  email: string;
  role_type: SupportTicketRoleType;
  category: SupportTicketCategory;
  priority: SupportTicketPriority;
  subject: string;
  message?: string;
  status: SupportTicketStatus;
  user_id?: number | null;
  assigned_admin_id?: number | null;
  admin_note?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  closed_at?: string | null;
  source: string;
  email_warning?: string | null;
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
