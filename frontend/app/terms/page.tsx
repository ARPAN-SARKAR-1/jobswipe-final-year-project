import Link from "next/link";

export default function TermsPage() {
  return (
    <main className="page-shell">
      <div className="panel mx-auto max-w-3xl p-8">
        <p className="mb-2 text-sm font-black uppercase text-teal-700">JobSwipe</p>
        <h1 className="text-4xl font-black tracking-normal">Terms and Conditions</h1>
        <div className="mt-6 space-y-4 text-sm font-medium leading-7 text-[#526069]">
          <p>Users must provide accurate account, profile, resume, company, job, and application information.</p>
          <p>Recruiters must post genuine jobs only. Fake jobs, misleading posts, abusive conduct, spam, and asking job seekers for money are prohibited.</p>
          <p>Job seekers must use applications and chat responsibly and must not harass, spam, or misuse recruiter communication.</p>
          <p>Owner/Admin users may pause or remove jobs, pause applications or chats, review reports, and suspend accounts for platform safety.</p>
          <p>Recruiters must clearly disclose bond or service agreement details wherever applicable.</p>
          <p>JobSwipe does not guarantee interviews, selection, placement, stipend, salary, or employer authenticity. Users should verify job authenticity before sharing sensitive information.</p>
          <p>JobSwipe is a final year project/demo platform and should be extended with production-grade compliance, legal review, and cloud storage controls before commercial use.</p>
          <p>By registering, users agree to follow these platform rules and the Privacy Policy.</p>
        </div>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/privacy" className="btn-secondary">Privacy Policy</Link>
          <Link href="/register" className="btn-primary">Back to Register</Link>
        </div>
      </div>
    </main>
  );
}
