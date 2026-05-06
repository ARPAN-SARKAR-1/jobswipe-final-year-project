export type Role = "JOB_SEEKER" | "RECRUITER" | "ADMIN" | "OWNER";

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
  created_at: string;
  updated_at: string;
};

export type CompanyProfile = {
  id: number;
  recruiter_id: number;
  company_name?: string | null;
  company_logo_url?: string | null;
  website?: string | null;
  description?: string | null;
  location?: string | null;
  recruiter_verification_status: "PENDING" | "VERIFIED" | "REJECTED";
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
