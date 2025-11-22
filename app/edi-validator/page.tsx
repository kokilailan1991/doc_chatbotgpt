"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { FileCheck, Upload, Sparkles, Copy, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const SAMPLE_BAPLIE = `UNH+1+BAPLIE:D:95B:UN'
BGM+85+12345678+9'
DTM+137:20240115:102'
NAD+MS+SHIPPER:172:123456789'
LOC+5+USNYC:139:6'
LOC+8+DEHAM:139:6'
EQD+CN+CONTAINER1234567+22G1+2200'
MEA+AAE+VGM+KGM:18500'
STS+1+1+1'
EQD+CN+CONTAINER7654321+22G1+2200'
MEA+AAE+VGM+KGM:19200'
STS+1+2+2'
CNT+2:2'
UNT+10+1'`;

export default function EDIValidatorPage() {
  const [file, setFile] = useState<File | null>(null);
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
      setError("Please upload an EDI file");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/analyze-edi", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Validation failed");
      }

      setResult(data);
      // Auto-scroll to results
      setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: any) {
      setError(err.message || "Failed to validate EDI file");
    } finally {
      setLoading(false);
    }
  };

  const handleSampleEDI = () => {
    const blob = new Blob([SAMPLE_BAPLIE], { type: "text/plain" });
    const sampleFile = new File([blob], "sample-baplie.edi", {
      type: "text/plain",
    });
    setFile(sampleFile);
    setError(null);
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
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-emerald-100 px-4 py-2">
            <Sparkles className="h-4 w-4 text-emerald-600" />
            <span className="text-sm font-medium text-emerald-900">
              EDI File Validator
            </span>
          </div>
          <h1 className="mb-4 text-4xl font-bold text-slate-900 sm:text-5xl">
            EDI Validator
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-slate-600">
            Validate BAPLIE, MOVINS, and COPRAR files. Detect errors, validate
            container formats, and get instant feedback.
          </p>
        </motion.div>

        {/* Upload Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-lg"
        >
          <h2 className="mb-6 text-2xl font-semibold text-slate-900">
            Upload EDI File
          </h2>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <label className="flex cursor-pointer items-center gap-2 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-4 transition-colors hover:border-emerald-400 hover:bg-emerald-50 flex-1">
              <Upload className="h-5 w-5 text-slate-600" />
              <span className="text-sm font-medium text-slate-700">
                {file ? file.name : "Choose .edi, .txt, .baplie, .movins, or .coprar file"}
              </span>
              <input
                type="file"
                accept=".edi,.txt,.baplie,.movins,.coprar"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
            <Button
              variant="outline"
              onClick={handleSampleEDI}
              className="whitespace-nowrap"
            >
              Try Sample BAPLIE
            </Button>
          </div>

          {file && (
            <p className="mt-4 text-sm text-slate-500">
              Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </p>
          )}

          <Button
            onClick={handleAnalyze}
            disabled={!file || loading}
            className="mt-6 w-full bg-gradient-to-r from-emerald-600 to-teal-600 text-lg py-6"
            size="lg"
          >
            {loading ? (
              <>
                <Sparkles className="mr-2 h-5 w-5 animate-spin" />
                Validating...
              </>
            ) : (
              <>
                <FileCheck className="mr-2 h-5 w-5" />
                Validate EDI File
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

        {/* Results Section */}
        {result && (
          <div id="results" className="space-y-6">
            {/* Summary Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-blue-200 bg-blue-50 p-6"
            >
              <h3 className="mb-4 text-xl font-semibold text-blue-900">
                Summary
              </h3>
              <p className="text-blue-800">{result.summary}</p>
            </motion.div>

            {/* Errors Card */}
            {result.errors?.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-red-200 bg-red-50 p-6"
              >
                <h3 className="mb-4 flex items-center gap-2 text-xl font-semibold text-red-900">
                  <AlertCircle className="h-5 w-5" />
                  Errors ({result.errors.length})
                </h3>
                <ul className="space-y-2">
                  {result.errors.map((err: string, idx: number) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-sm text-red-800"
                    >
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-red-500" />
                      {err}
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}

            {/* Warnings Card */}
            {result.warnings?.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-amber-200 bg-amber-50 p-6"
              >
                <h3 className="mb-4 text-xl font-semibold text-amber-900">
                  Warnings ({result.warnings.length})
                </h3>
                <ul className="space-y-2">
                  {result.warnings.map((warn: string, idx: number) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-sm text-amber-800"
                    >
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500" />
                      {warn}
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}

            {/* Suggestions Card */}
            {result.suggestions?.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-green-200 bg-green-50 p-6"
              >
                <h3 className="mb-4 flex items-center gap-2 text-xl font-semibold text-green-900">
                  <CheckCircle2 className="h-5 w-5" />
                  Suggested Fixes
                </h3>
                <ul className="space-y-2">
                  {result.suggestions.map((suggestion: string, idx: number) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-sm text-green-800"
                    >
                      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}

            {/* Containers Table */}
            {result.containers?.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg"
              >
                <div className="bg-slate-50 px-6 py-4">
                  <h3 className="text-xl font-semibold text-slate-900">
                    Containers ({result.containers.length})
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-700">
                          Container Number
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-700">
                          Size
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-700">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-700">
                          Weight (kg)
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {result.containers.map((container: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-6 py-4 font-mono text-sm text-slate-900">
                            {container.containerNumber || "N/A"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-700">
                            {container.size || "N/A"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-700">
                            {container.type || "N/A"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-700">
                            {container.weight || "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

