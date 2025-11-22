import { NextRequest, NextResponse } from "next/server";
import { validateEDIContent } from "@/lib/ai/edi-validator";
import { callLLM } from "@/lib/ai/llm-wrapper";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json(
        { error: "No file provided" },
        { status: 400 }
      );
    }

    // Detect file type by extension
    const fileName = file.name.toLowerCase();
    const isEDIFile =
      fileName.endsWith(".edi") ||
      fileName.endsWith(".txt") ||
      fileName.endsWith(".baplie") ||
      fileName.endsWith(".movins") ||
      fileName.endsWith(".coprar");

    if (!isEDIFile) {
      return NextResponse.json(
        { error: "Invalid file type. Expected .edi, .txt, .baplie, .movins, or .coprar" },
        { status: 400 }
      );
    }

    // Read as text
    const text = await file.text();

    // Run validation rules
    const validation = validateEDIContent(text);

    // Send to LLM for enhanced analysis
    const llmResult = await callLLM({
      system: `You are an expert EDI validator specializing in BAPLIE, MOVINS, and COPRAR formats.
Analyze the EDI content and provide structured insights.`,
      user: `Analyze this EDI file:

${text.substring(0, 5000)}

Validation results:
- Errors: ${validation.errors.length}
- Warnings: ${validation.warnings.length}
- Containers: ${validation.containers.length}

Provide:
1. Summary of file structure
2. Key issues found
3. Recommendations for fixes
4. Format compliance check`,
      temperature: 0.3,
      responseFormat: "json_object",
    });

    const aiAnalysis = llmResult.success ? llmResult.data : null;

    return NextResponse.json({
      success: true,
      errors: validation.errors,
      warnings: validation.warnings,
      summary: validation.summary,
      containers: validation.containers,
      suggestions: validation.suggestions,
      aiAnalysis,
      raw: text.substring(0, 1000), // Limit raw output
    });
  } catch (error: any) {
    console.error("EDI analysis error:", error);
    return NextResponse.json(
      { error: error?.message || "Failed to analyze EDI file" },
      { status: 500 }
    );
  }
}

