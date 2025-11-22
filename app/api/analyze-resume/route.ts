import { NextRequest, NextResponse } from "next/server";
import pdf from "pdf-parse";
import { callLLM } from "@/lib/ai/llm-wrapper";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File;
    const jobDescription = formData.get("jobDescription") as string | null;

    if (!file) {
      return NextResponse.json(
        { error: "No file provided" },
        { status: 400 }
      );
    }

    // Extract text from PDF
    let resumeText = "";
    const buffer = Buffer.from(await file.arrayBuffer());

    try {
      const pdfData = await pdf(buffer);
      resumeText = pdfData.text;
    } catch (error) {
      // If not PDF, try as text
      resumeText = await file.text();
    }

    if (!resumeText.trim()) {
      return NextResponse.json(
        { error: "Could not extract text from file" },
        { status: 400 }
      );
    }

    // Build prompt
    const jdContext = jobDescription
      ? `\n\nJob Description:\n${jobDescription}`
      : "";

    const llmResult = await callLLM({
      system: `You are an expert ATS (Applicant Tracking System) resume analyzer and career coach.
Analyze resumes for ATS compatibility, skills matching, and provide actionable feedback.
Return structured JSON with scores, strengths, weaknesses, and recommendations.`,
      user: `Analyze this resume${jobDescription ? " against the job description" : ""}:

${resumeText.substring(0, 8000)}${jdContext}

Provide:
1. ATS Score (0-100) - based on formatting, keywords, structure
2. Skills Match % (0-100) - if JD provided
3. JD Match Score (0-100) - overall fit if JD provided
4. Strengths (array of strings)
5. Weaknesses (array of strings)
6. Keyword recommendations (array of missing keywords)
7. Rewritten resume sections (structured JSON with: summary, experience, skills, education)
8. Executive summary (2-3 sentences)
9. Action items (array of specific improvements)`,
      temperature: 0.3,
      responseFormat: "json_object",
    });

    if (!llmResult.success) {
      return NextResponse.json(
        { error: llmResult.error || "Failed to analyze resume" },
        { status: 500 }
      );
    }

    const analysis = llmResult.data as any;

    return NextResponse.json({
      success: true,
      atsScore: analysis.atsScore || 0,
      skillsMatch: analysis.skillsMatch || null,
      jdMatchScore: analysis.jdMatchScore || null,
      strengths: analysis.strengths || [],
      weaknesses: analysis.weaknesses || [],
      keywordRecommendations: analysis.keywordRecommendations || [],
      rewrittenResume: analysis.rewrittenResume || {},
      executiveSummary: analysis.executiveSummary || "",
      actionItems: analysis.actionItems || [],
    });
  } catch (error: any) {
    console.error("Resume analysis error:", error);
    return NextResponse.json(
      { error: error?.message || "Failed to analyze resume" },
      { status: 500 }
    );
  }
}

