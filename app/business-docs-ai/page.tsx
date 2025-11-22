"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Briefcase, Upload, Sparkles, FileText, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function BusinessDocsAIPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("auto");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please upload a document");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("docType", docType);

      const response = await fetch("/api/analyze-business-doc", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze document");
    } finally {
      setLoading(false);
    }
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
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-purple-100 px-4 py-2">
            <Sparkles className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-900">
              Business Document Analyzer
            </span>
          </div>
          <h1 className="mb-4 text-4xl font-bold text-slate-900 sm:text-5xl">
            Business Docs Analyzer
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-slate-600">
            Analyze invoices, contracts, salary slips, proposals, and reports.
            Extract key data, detect risks, and get actionable insights.
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
                Upload Document
              </h2>

              {/* Document Type */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Document Type
                </label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                >
                  <option value="auto">Auto-detect</option>
                  <option value="invoice">Invoice</option>
                  <option value="contract">Contract</option>
                  <option value="salary_slip">Salary Slip</option>
                  <option value="proposal">Proposal</option>
                  <option value="report">Report</option>
                </select>
              </div>

              {/* File Upload */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Document File (PDF or TXT)
                </label>
                <label className="flex cursor-pointer items-center gap-2 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-4 transition-colors hover:border-purple-400 hover:bg-purple-50">
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
                {file && (
                  <p className="mt-2 text-xs text-slate-500">
                    Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={!file || loading}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-lg py-6"
                size="lg"
              >
                {loading ? (
                  <>
                    <Sparkles className="mr-2 h-5 w-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Briefcase className="mr-2 h-5 w-5" />
                    Analyze Document
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
                    <AlertTriangle className="h-5 w-5" />
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
                className="space-y-6"
              >
                {/* Summary */}
                {result.summary && (
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg">
                    <h3 className="mb-3 text-lg font-semibold text-slate-900">
                      Summary
                    </h3>
                    <p className="text-sm text-slate-700">{result.summary}</p>
                  </div>
                )}

                {/* Key Insights */}
                {result.keyInsights?.length > 0 && (
                  <div className="rounded-2xl border border-blue-200 bg-blue-50 p-6">
                    <h3 className="mb-3 text-lg font-semibold text-blue-900">
                      Key Insights
                    </h3>
                    <ul className="space-y-2">
                      {result.keyInsights.map((insight: string, idx: number) => (
                        <li
                          key={idx}
                          className="flex items-start gap-2 text-sm text-blue-800"
                        >
                          <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Risks */}
                {result.risks?.length > 0 && (
                  <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
                    <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-red-900">
                      <AlertTriangle className="h-5 w-5" />
                      Risks & Red Flags
                    </h3>
                    <ul className="space-y-2">
                      {result.risks.map((risk: string, idx: number) => (
                        <li
                          key={idx}
                          className="flex items-start gap-2 text-sm text-red-800"
                        >
                          <span className="mt-1 h-1.5 w-1.5 rounded-full bg-red-500" />
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action Items */}
                {result.actionItems?.length > 0 && (
                  <div className="rounded-2xl border border-green-200 bg-green-50 p-6">
                    <h3 className="mb-3 text-lg font-semibold text-green-900">
                      Action Items
                    </h3>
                    <ul className="space-y-2">
                      {result.actionItems.map((item: string, idx: number) => (
                        <li
                          key={idx}
                          className="flex items-start gap-2 text-sm text-green-800"
                        >
                          <FileText className="mt-0.5 h-4 w-4 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}

            {!result && (
              <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-12 text-center">
                <Briefcase className="mx-auto mb-4 h-12 w-12 text-slate-400" />
                <p className="text-sm text-slate-500">
                  Upload a document to see analysis results here
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

