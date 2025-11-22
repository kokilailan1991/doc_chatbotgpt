import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Business Document Analyzer – Invoices & Contracts | AIGPT",
  description:
    "Free AI-powered business document analyzer for invoices, contracts, salary slips, proposals, and reports. Extract key data and detect risks.",
  openGraph: {
    title: "AI Business Document Analyzer – Invoices & Contracts | AIGPT",
    description:
      "Analyze invoices, contracts, salary slips, proposals, and reports with AI. Extract key data and detect risks.",
    url: "https://bot.aigpt.co.in/business-docs-ai",
    type: "website",
  },
};

export default function BusinessDocsAILayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

