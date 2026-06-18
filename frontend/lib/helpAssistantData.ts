export type HelpAudience = "visitor" | "jobseeker" | "recruiter" | "admin" | "owner";

export type HelpTopic = {
  id: string;
  title: string;
  keywords: string[];
  pages?: string[];
  audience?: HelpAudience[];
  answer: string;
  steps?: string[];
  links?: Array<{ label: string; href: string }>;
};

export const helpTopics: HelpTopic[] = [
  {
    id: "what-is-jobseeker",
    title: "What is a Job Seeker?",
    keywords: ["job seeker", "student", "candidate", "apply", "internship"],
    pages: ["/", "/register", "/login"],
    audience: ["visitor", "jobseeker"],
    answer:
      "A Job Seeker is a user looking for internships or jobs. Job Seekers can create a profile, upload a resume, save jobs, apply to jobs, and build a public profile.",
    links: [{ label: "Join as Job Seeker", href: "/register" }]
  },
  {
    id: "what-is-recruiter",
    title: "What is a Recruiter?",
    keywords: ["recruiter", "hiring", "company", "post job", "applicants"],
    pages: ["/", "/register", "/login", "/recruiter"],
    audience: ["visitor", "recruiter"],
    answer:
      "A Recruiter represents a company or hiring team. Recruiters can create company profiles, post jobs, review applicants, and manage hiring workflows after verification.",
    links: [{ label: "Join as Recruiter", href: "/register" }]
  },
  {
    id: "cannot-login",
    title: "I cannot login",
    keywords: ["login", "sign in", "failed", "password", "portal", "otp", "captcha"],
    pages: ["/login", "/verify-login", "/forgot-password"],
    audience: ["visitor", "jobseeker", "recruiter", "admin", "owner"],
    answer: "Login usually fails because of an incorrect portal selection, password, CAPTCHA, or OTP step.",
    steps: [
      "Check that you selected the correct portal: Job Seeker, Recruiter, Admin, or Owner.",
      "Use the same email you registered with.",
      "Complete CAPTCHA.",
      "If you forgot your password, use Forgot Password.",
      "If OTP is required, check inbox/spam and use Resend OTP.",
      "If still blocked, raise a support ticket."
    ],
    links: [
      { label: "Forgot Password", href: "/forgot-password" },
      { label: "Raise support ticket", href: "/contact" }
    ]
  },
  {
    id: "no-account",
    title: "I do not have an account",
    keywords: ["account", "register", "join", "signup", "new user"],
    pages: ["/", "/login", "/register"],
    audience: ["visitor"],
    answer: "Create an account from the Register page and choose the account type that matches how you use the portal.",
    steps: [
      "Click Register or Join.",
      "Select Job Seeker if you are looking for jobs or internships.",
      "Select Recruiter if you are hiring for a company.",
      "Complete email verification."
    ],
    links: [{ label: "Register", href: "/register" }]
  },
  {
    id: "wrong-portal",
    title: "I selected the wrong portal",
    keywords: ["wrong portal", "role", "job seeker portal", "recruiter portal", "admin portal", "owner portal"],
    pages: ["/login"],
    audience: ["visitor", "jobseeker", "recruiter", "admin", "owner"],
    answer:
      "Each account belongs to one role. A Job Seeker account cannot login through the Recruiter portal. Select the correct portal for your account."
  },
  {
    id: "captcha-not-loading",
    title: "CAPTCHA is not loading",
    keywords: ["captcha", "security puzzle", "image", "not loading", "failed to fetch"],
    pages: ["/login", "/register", "/forgot-password", "/contact"],
    audience: ["visitor", "jobseeker", "recruiter", "admin", "owner"],
    answer: "CAPTCHA may take a moment if the server is waking up or the network is slow.",
    steps: [
      "Refresh the CAPTCHA.",
      "Check your internet connection.",
      "Wait a few seconds if the server is waking up.",
      "Try again after a few seconds.",
      "Raise a support ticket if it continues."
    ],
    links: [{ label: "Contact support", href: "/contact" }]
  },
  {
    id: "otp-not-received",
    title: "OTP not received",
    keywords: ["otp", "email", "verification", "resend", "code", "spam"],
    pages: ["/verify-email", "/verify-login", "/login", "/register"],
    audience: ["visitor", "jobseeker", "recruiter", "admin", "owner"],
    answer: "OTP emails can be delayed or filtered by your inbox provider.",
    steps: [
      "Check inbox, spam, and promotions.",
      "Wait one minute.",
      "Click Resend OTP.",
      "Confirm the email spelling.",
      "Raise a ticket if it still does not arrive."
    ],
    links: [{ label: "Raise support ticket", href: "/contact" }]
  },
  {
    id: "cannot-apply",
    title: "Why can’t I apply for a job?",
    keywords: ["apply", "blocked", "profile incomplete", "missing fields", "resume", "skills"],
    pages: ["/jobseeker/jobs", "/jobseeker/swipe", "/jobseeker/settings/profile"],
    audience: ["jobseeker"],
    answer:
      "You may need to complete your profile before applying. Required details include verified email, phone, skills, resume, category, and category-specific education or experience details.",
    steps: [
      "Go to Job Seeker Profile Settings.",
      "Complete missing fields.",
      "Upload resume.",
      "Add skills.",
      "Save profile.",
      "Try applying again."
    ],
    links: [{ label: "Complete profile", href: "/jobseeker/settings/profile" }]
  },
  {
    id: "jobseeker-categories",
    title: "What is Undergraduate / Graduate Fresher / Graduate Experienced?",
    keywords: ["undergraduate", "graduate fresher", "graduate experienced", "category", "student"],
    pages: ["/jobseeker/settings/profile", "/jobseeker/profile"],
    audience: ["jobseeker"],
    answer:
      "Undergraduate means you are currently studying and looking for internships or early opportunities. Graduate Fresher means you completed graduation and are looking for a first full-time role. Graduate Experienced means you have prior work experience."
  },
  {
    id: "student-proof",
    title: "Why do I need to upload student proof?",
    keywords: ["student proof", "college id", "library card", "bonafide", "documents", "private"],
    pages: ["/jobseeker/settings/profile"],
    audience: ["jobseeker"],
    answer:
      "Student proof helps prevent fake college claims and protects college/company reputation. These documents are private and used only for verification."
  },
  {
    id: "private-documents",
    title: "What documents are private?",
    keywords: ["private documents", "resume", "marksheet", "salary slip", "experience letter", "privacy"],
    pages: ["/jobseeker/settings/profile", "/u/"],
    audience: ["jobseeker", "recruiter"],
    answer:
      "College ID, library card, marksheets, experience letters, salary slips, and verification documents are private by default. Public profile pages do not expose private file URLs."
  },
  {
    id: "save-job",
    title: "How to save a job?",
    keywords: ["save job", "saved", "bookmark"],
    pages: ["/jobseeker/jobs", "/jobseeker/swipe", "/jobseeker/saved"],
    audience: ["jobseeker"],
    answer: "Saved jobs let you return to an opportunity later without applying immediately.",
    steps: ["Open Jobs or Swipe page.", "Click Save.", "View saved jobs from Saved Jobs page."],
    links: [{ label: "Saved Jobs", href: "/jobseeker/saved" }]
  },
  {
    id: "apply-from-swipe",
    title: "How to apply from swipe page?",
    keywords: ["swipe", "apply", "skip", "save", "career link"],
    pages: ["/jobseeker/swipe"],
    audience: ["jobseeker"],
    answer: "The swipe page lets you review one job at a time and apply quickly after checking the details.",
    steps: [
      "Review the job card.",
      "Check company details and official career link.",
      "Click Apply.",
      "If your profile is incomplete, complete missing profile fields first."
    ]
  },
  {
    id: "application-blocked",
    title: "Why is my application blocked?",
    keywords: ["application blocked", "expired", "paused", "removed", "already applied"],
    pages: ["/jobseeker/jobs", "/jobseeker/swipe", "/jobseeker/applications"],
    audience: ["jobseeker"],
    answer:
      "Applications can be blocked if your profile is incomplete, the job is expired, paused, removed, or you already applied."
  },
  {
    id: "cannot-post-job",
    title: "Why can’t I post a job?",
    keywords: ["post job", "company profile", "verification", "missing", "career page"],
    pages: ["/recruiter/jobs/new", "/recruiter/company", "/recruiter/dashboard"],
    audience: ["recruiter"],
    answer:
      "Recruiters must complete company profile and verification requirements before posting jobs. Required company details include company name, industry, company size, headquarters/location, official website, career page URL, company description, and recruiter title.",
    links: [{ label: "Complete company profile", href: "/recruiter/company" }]
  },
  {
    id: "career-url-required",
    title: "Why is career page URL required?",
    keywords: ["career url", "career page", "official link", "job authenticity", "ats"],
    pages: ["/recruiter/jobs/new", "/recruiter/company", "/jobseeker/jobs"],
    audience: ["jobseeker", "recruiter"],
    answer: "Official career links help users verify job authenticity and reduce fake job posts."
  },
  {
    id: "company-verification",
    title: "What is company verification?",
    keywords: ["company verification", "verified company", "blue tick", "trust"],
    pages: ["/recruiter/company", "/companies/", "/admin/dashboard"],
    audience: ["recruiter", "jobseeker", "admin", "owner"],
    answer:
      "Company verification confirms that the company profile is genuine. Verified companies can display a blue tick and build trust with applicants."
  },
  {
    id: "recruiter-verification",
    title: "What is recruiter verification?",
    keywords: ["recruiter verification", "authorized", "company member", "blue tick"],
    pages: ["/recruiter/company", "/recruiter/dashboard", "/admin/dashboard"],
    audience: ["recruiter", "admin", "owner"],
    answer: "Recruiter verification confirms that the recruiter is authorized to represent the company."
  },
  {
    id: "review-applicants",
    title: "How to review applicants?",
    keywords: ["applicants", "applications", "shortlist", "reject", "filter"],
    pages: ["/recruiter/applications"],
    audience: ["recruiter"],
    answer: "Use the recruiter applications page to search, filter, and review applicants.",
    steps: [
      "Go to Recruiter Applications.",
      "Use search/filter/sort.",
      "Open applicant details.",
      "Shortlist or reject based on profile and verification status."
    ],
    links: [{ label: "Recruiter Applications", href: "/recruiter/applications" }]
  },
  {
    id: "job-hidden",
    title: "Why is my job hidden?",
    keywords: ["hidden job", "paused", "removed", "deadline", "suspicious link", "unverified"],
    pages: ["/recruiter/dashboard", "/recruiter/jobs/new", "/admin/dashboard"],
    audience: ["recruiter", "admin", "owner"],
    answer:
      "A job can be hidden if the company is unverified, the job is paused or removed, the deadline expired, or Admin flagged a suspicious link."
  },
  {
    id: "admin-role",
    title: "What does Admin do?",
    keywords: ["admin", "moderation", "verification", "tickets", "reports"],
    pages: ["/admin/dashboard"],
    audience: ["admin", "owner"],
    answer:
      "Admin reviews verification requests, manages users, checks suspicious jobs, handles support tickets, and moderates platform activity."
  },
  {
    id: "owner-role",
    title: "What does Owner do?",
    keywords: ["owner", "protected", "highest access", "admin"],
    pages: ["/admin/dashboard"],
    audience: ["owner"],
    answer: "Owner has highest-level administrative access and can manage protected platform controls."
  },
  {
    id: "handle-support-tickets",
    title: "How to handle support tickets?",
    keywords: ["support tickets", "ticket status", "open", "resolved", "closed"],
    pages: ["/admin/dashboard", "/contact"],
    audience: ["admin", "owner"],
    answer: "Support tickets help track user issues from creation through resolution.",
    steps: [
      "Open Admin Dashboard.",
      "Go to Support Tickets.",
      "Check priority, status, and category.",
      "Mark in progress, resolved, or closed."
    ]
  },
  {
    id: "review-testimonials",
    title: "How to review company testimonials?",
    keywords: ["company testimonial", "review testimonial", "approve", "reject", "company provided"],
    pages: ["/admin/dashboard", "/recruiter/company", "/companies/"],
    audience: ["admin", "owner", "recruiter"],
    answer:
      "Company-provided testimonials should be approved only when they are safe, professional, and not misleading. Public testimonials are labeled as company-provided."
  },
  {
    id: "contact-ticket",
    title: "How support tickets work",
    keywords: ["contact", "support", "ticket code", "priority", "status", "email"],
    pages: ["/contact"],
    audience: ["visitor", "jobseeker", "recruiter", "admin", "owner"],
    answer:
      "When you submit the Contact Support form, Swipe for Success creates a ticket code and status. Ticket statuses are Open, In Progress, Resolved, and Closed. Support email is also available on the Contact page.",
    steps: [
      "Fill in your name, email, role, category, priority, subject, and message.",
      "Solve the security puzzle.",
      "Save the ticket code shown after submission.",
      "Use support email if you need an alternate contact method."
    ],
    links: [{ label: "Contact Support", href: "/contact" }]
  },
  {
    id: "raise-ticket",
    title: "Need more help?",
    keywords: ["help", "support", "contact", "ticket", "issue"],
    pages: ["/"],
    audience: ["visitor", "jobseeker", "recruiter", "admin", "owner"],
    answer: "If the assistant cannot answer your question, raise a support ticket and the team will review it.",
    links: [{ label: "Raise a support ticket", href: "/contact" }]
  }
];

export function getRouteSuggestedTopics(pathname: string, role?: HelpAudience): HelpTopic[] {
  const normalized = pathname || "/";
  const scored = helpTopics
    .map((topic) => {
      const pageScore = topic.pages?.some((page) => (page === "/" ? normalized === "/" : normalized === page || normalized.startsWith(page))) ? 3 : 0;
      const roleScore = role && topic.audience?.includes(role) ? 2 : topic.audience?.includes("visitor") ? 1 : 0;
      return { topic, score: pageScore + roleScore };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.topic.title.localeCompare(b.topic.title));
  return scored.slice(0, 6).map((item) => item.topic);
}

export function searchHelpTopics(query: string, role?: HelpAudience): HelpTopic[] {
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  if (terms.length === 0) return [];
  return helpTopics
    .map((topic) => {
      const haystack = [topic.title, topic.answer, ...(topic.keywords || []), ...(topic.steps || [])].join(" ").toLowerCase();
      const roleBoost = role && topic.audience?.includes(role) ? 1 : 0;
      const score = terms.reduce((total, term) => total + (haystack.includes(term) ? 1 : 0), roleBoost);
      return { topic, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.topic.title.localeCompare(b.topic.title))
    .slice(0, 8)
    .map((item) => item.topic);
}
