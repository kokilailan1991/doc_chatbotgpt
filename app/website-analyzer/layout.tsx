import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Website Analyzer – SEO & Content Summary | AIGPT",
  description:
    "Free AI-powered website analyzer for SEO score, content quality analysis, structure review, and optimization recommendations.",
  openGraph: {
    title: "AI Website Analyzer – SEO & Content Summary | AIGPT",
    description:
      "Get instant SEO score, content quality analysis, and optimization recommendations for any website.",
    url: "https://bot.aigpt.co.in/website-analyzer",
    type: "website",
  },
};

export default function WebsiteAnalyzerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

