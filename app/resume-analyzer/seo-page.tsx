import type { Metadata } from "next";
import Link from "next/link";
import { FileText, CheckCircle2, ArrowRight } from "lucide-react";

export const metadata: Metadata = {
  title: "AI Resume Analyzer – Free ATS Score & JD Match | AIGPT",
  description:
    "Free AI-powered resume analyzer with ATS score, job description matching, and keyword optimization. Get instant feedback to improve your resume and land more interviews.",
  openGraph: {
    title: "AI Resume Analyzer – Free ATS Score & JD Match | AIGPT",
    description:
      "Get instant ATS score, JD match percentage, and AI-powered recommendations to improve your resume.",
    url: "https://bot.aigpt.co.in/resume-analyzer",
    type: "website",
  },
};

const faqs = [
  {
    question: "What is an ATS score?",
    answer:
      "ATS (Applicant Tracking System) score measures how well your resume is formatted and optimized for automated screening systems used by employers. A higher score means better compatibility with these systems.",
  },
  {
    question: "How accurate is the JD match score?",
    answer:
      "Our AI analyzes your resume against the job description using advanced NLP techniques. The match score indicates how well your skills and experience align with the job requirements.",
  },
  {
    question: "Do I need to create an account?",
    answer:
      "No! Our resume analyzer is completely free and requires no login or account creation. Just upload your resume and get instant results.",
  },
  {
    question: "What file formats are supported?",
    answer:
      "We support PDF and TXT formats. PDF is recommended for best results as it preserves formatting.",
  },
  {
    question: "Is my resume data secure?",
    answer:
      "Yes! We process your resume securely and don't store it permanently. Your data is only used for analysis and is deleted after processing.",
  },
  {
    question: "Can I use this for multiple job applications?",
    answer:
      "Absolutely! You can analyze your resume multiple times with different job descriptions to optimize it for each application.",
  },
  {
    question: "What makes this different from other resume analyzers?",
    answer:
      "Our AI provides detailed keyword recommendations, rewritten resume sections, and actionable insights - not just a score. Plus, it's completely free with no limits.",
  },
];

export default function ResumeAnalyzerSEOPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "AI Resume Analyzer",
    applicationCategory: "BusinessApplication",
    description:
      "Free AI-powered resume analyzer with ATS score, job description matching, and keyword optimization",
    url: "https://bot.aigpt.co.in/resume-analyzer",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    featureList: [
      "ATS Score Calculation",
      "Job Description Matching",
      "Keyword Recommendations",
      "Resume Section Rewriting",
      "Skills Match Analysis",
    ],
  };

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />

      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
        <div className="container mx-auto max-w-4xl px-4 py-16">
          {/* Header */}
          <div className="mb-12 text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-blue-100 px-4 py-2">
              <FileText className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">
                Free AI Tool
              </span>
            </div>
            <h1 className="mb-4 text-4xl font-bold text-slate-900 sm:text-5xl">
              AI Resume Analyzer – Free ATS Score & JD Match
            </h1>
            <p className="text-lg text-slate-600">
              Get instant feedback on your resume with AI-powered analysis
            </p>
          </div>

          {/* CTA */}
          <div className="mb-16 text-center">
            <Link
              href="/resume-analyzer"
              className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-4 text-lg font-semibold text-white shadow-lg transition-transform hover:scale-105"
            >
              Try Resume Analyzer Now
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>

          {/* SEO Content */}
          <div className="prose prose-slate mx-auto max-w-none">
            <h2>What is a Resume Analyzer?</h2>
            <p>
              A resume analyzer is an AI-powered tool that evaluates your resume
              for ATS (Applicant Tracking System) compatibility, keyword
              optimization, and job description matching. Our free resume
              analyzer provides instant feedback to help you improve your resume
              and increase your chances of landing interviews.
            </p>

            <h2>Key Features</h2>
            <ul>
              <li>
                <strong>ATS Score (0-100):</strong> Measures how well your
                resume is formatted for automated screening systems
              </li>
              <li>
                <strong>JD Match Score:</strong> Compares your resume against
                job descriptions to show alignment
              </li>
              <li>
                <strong>Skills Match Percentage:</strong> Identifies how many
                required skills you have
              </li>
              <li>
                <strong>Keyword Recommendations:</strong> Suggests missing
                keywords to improve ATS compatibility
              </li>
              <li>
                <strong>Rewritten Sections:</strong> AI-generated improvements
                for summary, experience, and skills sections
              </li>
              <li>
                <strong>Strengths & Weaknesses:</strong> Detailed analysis of
                what works and what needs improvement
              </li>
            </ul>

            <h2>How It Works</h2>
            <ol>
              <li>Upload your resume (PDF or TXT format)</li>
              <li>
                Optionally paste a job description for targeted analysis
              </li>
              <li>Get instant AI-powered feedback</li>
              <li>Review scores, recommendations, and rewritten sections</li>
              <li>Improve your resume based on actionable insights</li>
            </ol>

            <h2>Why Use Our Resume Analyzer?</h2>
            <p>
              Most resumes are rejected by ATS systems before they even reach a
              human recruiter. Our AI resume analyzer helps you:
            </p>
            <ul>
              <li>Optimize your resume for ATS systems</li>
              <li>Match job descriptions more effectively</li>
              <li>Identify missing keywords and skills</li>
              <li>Improve resume structure and formatting</li>
              <li>Get personalized recommendations</li>
            </ul>

            <h2>Related Tools</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <Link
                href="/business-docs-ai"
                className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
              >
                <h3 className="font-semibold text-slate-900">
                  Business Docs Analyzer
                </h3>
                <p className="text-sm text-slate-600">
                  Analyze invoices, contracts, and business documents
                </p>
              </Link>
              <Link
                href="/edi-validator"
                className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
              >
                <h3 className="font-semibold text-slate-900">EDI Validator</h3>
                <p className="text-sm text-slate-600">
                  Validate BAPLIE, MOVINS, and COPRAR files
                </p>
              </Link>
              <Link
                href="/website-analyzer"
                className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
              >
                <h3 className="font-semibold text-slate-900">
                  Website Analyzer
                </h3>
                <p className="text-sm text-slate-600">
                  SEO analysis and content quality review
                </p>
              </Link>
            </div>
          </div>

          {/* FAQ Section */}
          <div className="mt-16">
            <h2 className="mb-8 text-3xl font-bold text-slate-900">
              Frequently Asked Questions
            </h2>
            <div className="space-y-6">
              {faqs.map((faq, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <h3 className="mb-2 flex items-center gap-2 text-lg font-semibold text-slate-900">
                    <CheckCircle2 className="h-5 w-5 text-blue-500" />
                    {faq.question}
                  </h3>
                  <p className="text-slate-600">{faq.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

