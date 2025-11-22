import { NextRequest, NextResponse } from "next/server";
import pdf from "pdf-parse";
import { callLLM } from "@/lib/ai/llm-wrapper";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File;
    const docType = (formData.get("docType") as string) || "auto";

    if (!file) {
      return NextResponse.json(
        { error: "No file provided" },
        { status: 400 }
      );
    }

    // Extract text from PDF
    let docText = "";
    const buffer = Buffer.from(await file.arrayBuffer());

    try {
      const pdfData = await pdf(buffer);
      docText = pdfData.text;
    } catch (error) {
      // If not PDF, try as text
      docText = await file.text();
    }

    if (!docText.trim()) {
      return NextResponse.json(
        { error: "Could not extract text from file" },
        { status: 400 }
      );
    }

    // Detect document type if auto
    let detectedType = docType;
    if (docType === "auto") {
      const lowerText = docText.toLowerCase();
      if (lowerText.includes("invoice") || lowerText.includes("bill")) {
        detectedType = "invoice";
      } else if (
        lowerText.includes("contract") ||
        lowerText.includes("agreement")
      ) {
        detectedType = "contract";
      } else if (
        lowerText.includes("salary") ||
        lowerText.includes("payslip")
      ) {
        detectedType = "salary_slip";
      } else if (lowerText.includes("proposal")) {
        detectedType = "proposal";
      } else {
        detectedType = "report";
      }
    }

    // Build prompt based on type
    const typePrompts: Record<string, string> = {
      invoice: `Analyze this invoice. Extract: total amount, due date, line items, tax breakdown, payment terms, vendor details, and any discrepancies.`,
      contract: `Analyze this contract. Extract: parties involved, key terms, obligations, payment terms, termination clauses, risks, and red flags.`,
      salary_slip: `Analyze this salary slip. Extract: gross salary, deductions, net salary, tax breakdown, allowances, and verify calculations.`,
      proposal: `Analyze this business proposal. Extract: objectives, pricing, timeline, deliverables, risks, and negotiation points.`,
      report: `Analyze this business report. Extract: key findings, metrics, trends, recommendations, and action items.`,
    };

    const systemPrompt = typePrompts[detectedType] || typePrompts.report;

    const llmResult = await callLLM({
      system: `You are an expert business document analyzer. ${systemPrompt}
Provide structured insights, extract key data, identify risks, and suggest action items.`,
      user: `Analyze this ${detectedType}:

${docText.substring(0, 10000)}

Provide:
1. Summary (2-3 sentences)
2. Key insights (array of important points)
3. Risks & red flags (array of concerns)
4. Financial extraction (if applicable - amounts, dates, terms)
5. Action items (array of specific next steps)
6. Negotiation points (if applicable - array of points to discuss)
7. Data tables (structured JSON with extracted data)`,
      temperature: 0.3,
      responseFormat: "json_object",
    });

    if (!llmResult.success) {
      return NextResponse.json(
        { error: llmResult.error || "Failed to analyze document" },
        { status: 500 }
      );
    }

    const analysis = llmResult.data as any;

    return NextResponse.json({
      success: true,
      docType: detectedType,
      summary: analysis.summary || "",
      keyInsights: analysis.keyInsights || [],
      risks: analysis.risks || [],
      financialExtraction: analysis.financialExtraction || {},
      actionItems: analysis.actionItems || [],
      negotiationPoints: analysis.negotiationPoints || [],
      dataTables: analysis.dataTables || {},
    });
  } catch (error: any) {
    console.error("Business doc analysis error:", error);
    return NextResponse.json(
      { error: error?.message || "Failed to analyze document" },
      { status: 500 }
    );
  }
}

