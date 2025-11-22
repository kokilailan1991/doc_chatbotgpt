import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Resume Analyzer – Free ATS Score & JD Match | AIGPT",
  description:
    "Free AI-powered resume analyzer with ATS score, job description matching, and keyword optimization. Get instant feedback to improve your resume.",
  openGraph: {
    title: "AI Resume Analyzer – Free ATS Score & JD Match | AIGPT",
    description:
      "Get instant ATS score, JD match percentage, and AI-powered recommendations to improve your resume.",
    url: "https://bot.aigpt.co.in/resume-analyzer",
    type: "website",
  },
};

export default function ResumeAnalyzerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

