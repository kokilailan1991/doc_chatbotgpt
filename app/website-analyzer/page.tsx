"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Globe, Sparkles, AlertCircle, CheckCircle2, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function WebsiteAnalyzerPage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!url.trim()) {
      setError("Please enter a URL");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/analyze-website", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze website");
    } finally {
      setLoading(false);
    }
  };

  const handleSample = () => {
    setUrl("https://example.com");
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
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-orange-100 px-4 py-2">
            <Sparkles className="h-4 w-4 text-orange-600" />
            <span className="text-sm font-medium text-orange-900">
              SEO & Content Analyzer
            </span>
          </div>
          <h1 className="mb-4 text-4xl font-bold text-slate-900 sm:text-5xl">
            Website Analyzer
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-slate-600">
            Get instant SEO score, content quality analysis, and optimization
            recommendations for any website
          </p>
        </motion.div>

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-lg"
        >
          <h2 className="mb-6 text-2xl font-semibold text-slate-900">
            Enter Website URL
          </h2>

          <div className="flex gap-4">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-sm focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-200"
            />
            <Button
              variant="outline"
              onClick={handleSample}
              className="whitespace-nowrap"
            >
              Try Sample
            </Button>
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={!url || loading}
            className="mt-6 w-full bg-gradient-to-r from-orange-600 to-red-600 text-lg py-6"
            size="lg"
          >
            {loading ? (
              <>
                <Sparkles className="mr-2 h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Globe className="mr-2 h-5 w-5" />
                Analyze Website
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
                <AlertCircle className="h-5 w-5" />
                <span className="font-medium">{error}</span>
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* SEO Score */}
            {result.seoAnalysis && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-orange-200 bg-gradient-to-br from-orange-50 to-red-50 p-8"
              >
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-2xl font-semibold text-slate-900">
                    SEO Score
                  </h3>
                  <div className="text-5xl font-bold text-orange-600">
                    {result.seoAnalysis.seoScore || 0}/100
                  </div>
                </div>
                <div className="h-4 w-full overflow-hidden rounded-full bg-slate-200">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{
                      width: `${result.seoAnalysis.seoScore || 0}%`,
                    }}
                    transition={{ duration: 1 }}
                    className="h-full bg-gradient-to-r from-orange-500 to-red-500"
                  />
                </div>
              </motion.div>
            )}

            {/* Metadata */}
            {result.metadata && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg"
              >
                <h3 className="mb-4 text-xl font-semibold text-slate-900">
                  Page Metadata
                </h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm font-medium text-slate-600">
                      Title:
                    </span>
                    <p className="text-slate-900">{result.metadata.title || "Missing"}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-slate-600">
                      Meta Description:
                    </span>
                    <p className="text-slate-700">
                      {result.metadata.metaDescription || "Missing"}
                    </p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Structure */}
            {result.structure && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg"
              >
                <h3 className="mb-4 text-xl font-semibold text-slate-900">
                  Page Structure
                </h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-600">H1 Headings</div>
                    <div className="text-2xl font-bold text-slate-900">
                      {result.structure.h1?.length || 0}
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-600">H2 Headings</div>
                    <div className="text-2xl font-bold text-slate-900">
                      {result.structure.h2?.length || 0}
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-600">Links</div>
                    <div className="text-2xl font-bold text-slate-900">
                      {result.structure.linksCount || 0}
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-600">Images</div>
                    <div className="text-2xl font-bold text-slate-900">
                      {result.structure.imagesCount || 0}
                    </div>
                    {result.structure.imagesWithoutAlt > 0 && (
                      <div className="mt-2 text-xs text-red-600">
                        {result.structure.imagesWithoutAlt} without alt text
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* SEO Analysis */}
            {result.seoAnalysis && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {result.seoAnalysis.issues && result.seoAnalysis.issues.length > 0 && (
                  <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
                    <h4 className="mb-3 flex items-center gap-2 text-lg font-semibold text-red-900">
                      <AlertCircle className="h-5 w-5" />
                      Issues & Warnings
                    </h4>
                    <ul className="space-y-2">
                      {result.seoAnalysis.issues.map((issue: string, idx: number) => (
                        <li key={idx} className="text-sm text-red-800">
                          • {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.seoAnalysis.opportunities && result.seoAnalysis.opportunities.length > 0 && (
                  <div className="rounded-2xl border border-green-200 bg-green-50 p-6">
                    <h4 className="mb-3 flex items-center gap-2 text-lg font-semibold text-green-900">
                      <TrendingUp className="h-5 w-5" />
                      Opportunities
                    </h4>
                    <ul className="space-y-2">
                      {result.seoAnalysis.opportunities.map(
                        (opp: string, idx: number) => (
                          <li key={idx} className="text-sm text-green-800">
                            • {opp}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

                {result.seoAnalysis.recommendations && result.seoAnalysis.recommendations.length > 0 && (
                  <div className="rounded-2xl border border-blue-200 bg-blue-50 p-6">
                    <h4 className="mb-3 flex items-center gap-2 text-lg font-semibold text-blue-900">
                      <CheckCircle2 className="h-5 w-5" />
                      Action Recommendations
                    </h4>
                    <ul className="space-y-2">
                      {result.seoAnalysis.recommendations.map(
                        (rec: string, idx: number) => (
                          <li key={idx} className="text-sm text-blue-800">
                            • {rec}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

