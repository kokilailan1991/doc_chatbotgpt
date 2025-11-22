import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "EDI Validator – BAPLIE, MOVINS, COPRAR Analyzer | AIGPT",
  description:
    "Free EDI file validator for BAPLIE, MOVINS, and COPRAR formats. Detect errors, validate container formats, and get instant feedback.",
  openGraph: {
    title: "EDI Validator – BAPLIE, MOVINS, COPRAR Analyzer | AIGPT",
    description:
      "Validate EDI files instantly. Detect errors, validate container formats, and get actionable feedback.",
    url: "https://bot.aigpt.co.in/edi-validator",
    type: "website",
  },
};

export default function EDIValidatorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

