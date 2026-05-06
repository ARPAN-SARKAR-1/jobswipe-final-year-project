import Link from "next/link";

const sections = [
  ["What data we collect", "Name, email, role, profile details, education, skills, experience, GitHub profile link, resume PDF, profile picture, company details, application activity, swipe activity, reports, notifications, and chat messages."],
  ["Why we collect data", "We use this data for account creation, job matching, application tracking, recruiter communication, platform safety, moderation, and support."],
  ["Resume visibility", "Your resume is not public. It becomes visible only to recruiters when you apply to their job. Owner/Admin may access it only for moderation or support if required."],
  ["Chat visibility", "Chat is visible to the recruiter and job seeker participating in the thread. Owner/Admin may access chat metadata, and moderation access may be used only for safety and abuse review."],
  ["Security", "Passwords are hashed, JWT authentication is used, and role-based access control protects job seeker, recruiter, admin, and owner workflows."],
  ["Data deletion", "Users may request account or data deletion in future scope. Production deployments should add a formal data deletion workflow."],
  ["Cookies and local storage", "JobSwipe may store a token/session in browser local storage to keep users logged in."],
  ["Disclaimer", "JobSwipe is a final year project/demo platform. Users should verify job authenticity before sharing sensitive personal or financial information."]
];

export default function PrivacyPage() {
  return (
    <main className="page-shell">
      <div className="panel mx-auto max-w-3xl p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">JobSwipe</p>
        <h1 className="text-4xl font-black tracking-normal">Privacy Policy</h1>
        <div className="mt-6 grid gap-4">
          {sections.map(([title, text]) => (
            <section key={title} className="rounded-lg border border-black/10 bg-white/70 p-4">
              <h2 className="font-black text-[#172026]">{title}</h2>
              <p className="mt-2 text-sm font-medium leading-7 text-[#526069]">{text}</p>
            </section>
          ))}
        </div>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/terms" className="btn-secondary">Terms</Link>
          <Link href="/register" className="btn-primary">Back to Register</Link>
        </div>
      </div>
    </main>
  );
}
