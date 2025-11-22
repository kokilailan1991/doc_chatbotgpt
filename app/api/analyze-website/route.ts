import { NextRequest, NextResponse } from "next/server";
import cheerio from "cheerio";
import { callLLM } from "@/lib/ai/llm-wrapper";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const url = body.url;

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 });
    }

    // Validate URL
    let targetUrl: URL;
    try {
      targetUrl = new URL(url);
    } catch {
      return NextResponse.json({ error: "Invalid URL format" }, { status: 400 });
    }

    // Fetch HTML server-side
    const response = await fetch(targetUrl.toString(), {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
      },
      redirect: "follow",
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Failed to fetch website: ${response.status} ${response.statusText}` },
        { status: response.status }
      );
    }

    const html = await response.text();
    const $ = cheerio.load(html);

    // Extract metadata
    const title = $("title").text().trim() || "";
    const metaDescription =
      $('meta[name="description"]').attr("content") || "";
    const metaKeywords =
      $('meta[name="keywords"]').attr("content") || "";

    // Extract headings
    const h1 = $("h1")
      .map((_, el) => $(el).text().trim())
      .get()
      .filter(Boolean);
    const h2 = $("h2")
      .map((_, el) => $(el).text().trim())
      .get()
      .filter(Boolean);

    // Extract text content (remove scripts, styles)
    $("script, style, noscript").remove();
    const textContent = $("body").text().replace(/\s+/g, " ").trim();

    // Count elements
    const linksCount = $("a").length;
    const imagesCount = $("img").length;
    const imagesWithAlt = $("img[alt]").length;
    const imagesWithoutAlt = imagesCount - imagesWithAlt;

    // Extract structured data
    const ogTitle = $('meta[property="og:title"]').attr("content") || "";
    const ogDescription =
      $('meta[property="og:description"]').attr("content") || "";
    const ogImage = $('meta[property="og:image"]').attr("content") || "";

    // Send to LLM for SEO analysis
    const llmResult = await callLLM({
      system: `You are an expert SEO analyst. Analyze website content and provide structured SEO insights.`,
      user: `Analyze this website:

URL: ${url}
Title: ${title}
Meta Description: ${metaDescription || "Missing"}
H1 Headings: ${h1.join(", ") || "None"}
H2 Headings: ${h2.slice(0, 10).join(", ") || "None"}
Text Content Length: ${textContent.length} characters
Links: ${linksCount}
Images: ${imagesCount} (${imagesWithoutAlt} without alt text)

Provide:
1. SEO Score (0-100)
2. Structure analysis
3. Content quality rating
4. Issues & warnings
5. Opportunities
6. Action recommendations
7. Keyword suggestions`,
      temperature: 0.5,
      responseFormat: "json_object",
    });

    const seoAnalysis = llmResult.success ? llmResult.data : null;

    return NextResponse.json({
      success: true,
      url,
      metadata: {
        title,
        metaDescription,
        metaKeywords,
        ogTitle,
        ogDescription,
        ogImage,
      },
      structure: {
        h1,
        h2: h2.slice(0, 20),
        linksCount,
        imagesCount,
        imagesWithAlt,
        imagesWithoutAlt,
        textLength: textContent.length,
      },
      seoAnalysis,
    });
  } catch (error: any) {
    console.error("Website analysis error:", error);
    return NextResponse.json(
      { error: error?.message || "Failed to analyze website" },
      { status: 500 }
    );
  }
}

