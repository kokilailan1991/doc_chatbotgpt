"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { FileText, Upload, Sparkles, Copy, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

const SAMPLE_RESUME = `John Doe
Software Engineer
Email: john.doe@email.com | Phone: +1-234-567-8900

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years in full-stack development. 
Expert in React, Node.js, and cloud technologies. Led multiple successful 
projects delivering scalable web applications.

EXPERIENCE
Senior Software Engineer | Tech Corp | 2020 - Present
- Developed and maintained React-based frontend applications
- Built RESTful APIs using Node.js and Express
- Implemented CI/CD pipelines reducing deployment time by 40%
- Led team of 3 junior developers

Software Engineer | Startup Inc | 2018 - 2020
- Built responsive web applications using React and TypeScript
- Collaborated with cross-functional teams on product features
- Optimized database queries improving performance by 30%

SKILLS
- Programming: JavaScript, TypeScript, Python, Java
- Frameworks: React, Node.js, Express, Django
- Databases: PostgreSQL, MongoDB, Redis
- Tools: Git, Docker, AWS, Kubernetes

EDUCATION
Bachelor of Science in Computer Science
State University | 2014 - 2018`;

export default function ResumeAnalyzerPage() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please upload a resume file");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (jobDescription.trim()) {
        formData.append("jobDescription", jobDescription);
      }

      const response = await fetch("/api/analyze-resume", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze resume");
    } finally {
      setLoading(false);
    }
  };

  const handleSampleResume = () => {
    const blob = new Blob([SAMPLE_RESUME], { type: "text/plain" });
    const sampleFile = new File([blob], "sample-resume.txt", {
      type: "text/plain",
    });
    setFile(sampleFile);
    setError(null);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto max-w-6xl px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-blue-100 px-4 py-2">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">
              AI-Powered Resume Analysis
            </span>
          </div>
          <h1 className="mb-4 text-4xl font-bold text-slate-900 sm:text-5xl">
            Resume Analyzer
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-slate-600">
            Get instant ATS score, JD match percentage, and AI-powered
            recommendations to improve your resume
          </p>
        </motion.div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Input Section */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="rounded-2xl border border-slate-200 bg-white p-8 shadow-lg"
            >
              <h2 className="mb-6 text-2xl font-semibold text-slate-900">
                Upload Your Resume
              </h2>

              {/* File Upload */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Resume File (PDF or TXT)
                </label>
                <div className="flex items-center gap-4">
                  <label className="flex cursor-pointer items-center gap-2 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-4 transition-colors hover:border-blue-400 hover:bg-blue-50">
                    <Upload className="h-5 w-5 text-slate-600" />
                    <span className="text-sm font-medium text-slate-700">
                      {file ? file.name : "Choose File"}
                    </span>
                    <input
                      type="file"
                      accept=".pdf,.txt"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSampleResume}
                  >
                    Try Sample Resume
                  </Button>
                </div>
                {file && (
                  <p className="mt-2 text-xs text-slate-500">
                    Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>

              {/* Job Description (Optional) */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Job Description (Optional - for JD matching)
                </label>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description here for targeted analysis..."
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  rows={6}
                />
              </div>

              {/* Analyze Button */}
              <Button
                onClick={handleAnalyze}
                disabled={!file || loading}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-lg py-6"
                size="lg"
              >
                {loading ? (
                  <>
                    <Sparkles className="mr-2 h-5 w-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-5 w-5" />
                    Analyze Resume
                  </>
                )}
              </Button>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4"
                >
                  <div className="flex items-center gap-2 text-red-800">
                    <XCircle className="h-5 w-5" />
                    <span className="font-medium">{error}</span>
                  </div>
                </motion.div>
              )}
            </motion.div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-1">
            {result && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg"
              >
                <div className="mb-6 flex items-center justify-between">
                  <h3 className="text-xl font-semibold text-slate-900">
                    Your Results
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      copyToClipboard(JSON.stringify(result, null, 2))
                    }
                  >
                    {copied ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                {/* ATS Score */}
                <div className="mb-6 rounded-xl bg-gradient-to-br from-blue-50 to-purple-50 p-6">
                  <div className="mb-2 text-sm font-medium text-slate-600">
                    ATS Score
                  </div>
                  <div className="text-4xl font-bold text-blue-600">
                    {result.atsScore}/100
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${result.atsScore}%` }}
                      transition={{ duration: 1 }}
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                    />
                  </div>
                </div>

                {/* JD Match Score */}
                {result.jdMatchScore !== null && (
                  <div className="mb-6 rounded-xl bg-emerald-50 p-6">
                    <div className="mb-2 text-sm font-medium text-slate-600">
                      JD Match Score
                    </div>
                    <div className="text-3xl font-bold text-emerald-600">
                      {result.jdMatchScore}%
                    </div>
                  </div>
                )}

                {/* Skills Match */}
                {result.skillsMatch !== null && (
                  <div className="mb-6 rounded-xl bg-amber-50 p-6">
                    <div className="mb-2 text-sm font-medium text-slate-600">
                      Skills Match
                    </div>
                    <div className="text-3xl font-bold text-amber-600">
                      {result.skillsMatch}%
                    </div>
                  </div>
                )}

                {/* Strengths */}
                {result.strengths?.length > 0 && (
                  <div className="mb-6">
                    <h4 className="mb-3 text-sm font-semibold text-slate-900">
                      Strengths
                    </h4>
                    <ul className="space-y-2">
                      {result.strengths.map((strength: string, idx: number) => (
                        <li
                          key={idx}
                          className="flex items-start gap-2 text-sm text-slate-700"
                        >
                          <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                          <span>{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Weaknesses */}
                {result.weaknesses?.length > 0 && (
                  <div className="mb-6">
                    <h4 className="mb-3 text-sm font-semibold text-slate-900">
                      Areas for Improvement
                    </h4>
                    <ul className="space-y-2">
                      {result.weaknesses.map(
                        (weakness: string, idx: number) => (
                          <li
                            key={idx}
                            className="flex items-start gap-2 text-sm text-slate-700"
                          >
                            <XCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-500" />
                            <span>{weakness}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

                {/* Executive Summary */}
                {result.executiveSummary && (
                  <div className="mb-6 rounded-lg bg-slate-50 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-slate-900">
                      Executive Summary
                    </h4>
                    <p className="text-sm text-slate-700">
                      {result.executiveSummary}
                    </p>
                  </div>
                )}
              </motion.div>
            )}

            {!result && (
              <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-12 text-center">
                <FileText className="mx-auto mb-4 h-12 w-12 text-slate-400" />
                <p className="text-sm text-slate-500">
                  Upload a resume to see analysis results here
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

