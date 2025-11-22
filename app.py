import os
import sys

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import Flask and basic dependencies
from flask import Flask, request, jsonify, send_from_directory, render_template, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import json
from datetime import datetime

# Import workflow modules
try:
    from workflows import WorkflowProcessor
    from resume_analyzer import ResumeAnalyzer
    from edi_analyzer import EDIAnalyzer
    from output_formats import OutputGenerator
    from business_docs_analyzer import BusinessDocsAnalyzer
    from website_analyzer import WebsiteAnalyzer
except ImportError as e:
    print(f"Warning: Could not import workflow modules: {e}")
    WorkflowProcessor = None
    ResumeAnalyzer = None
    EDIAnalyzer = None
    OutputGenerator = None
    BusinessDocsAnalyzer = None
    WebsiteAnalyzer = None

# Import other dependencies with error handling
try:
    import fitz  # PyMuPDF
    import requests
    from bs4 import BeautifulSoup
    
    # LangChain imports
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import CharacterTextSplitter
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
except ImportError as e:
    print(f"❌ Import error: {e}", file=sys.stderr)
    print("Please ensure all dependencies are installed.", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__, static_url_path="", static_folder=".", template_folder="templates")
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

retriever_cache = {}
chat_history_store = {}  # Store chat histories for sharing
file_store = {}  # Store multiple files for comparison

@app.route("/", methods=["GET"])
def serve_index():
    return render_template("index_workflow.html", 
                         page_title="AI Document Chatbot - Workflow-Driven Document Analysis",
                         meta_description="AI-powered workflow-driven document analysis. Resume analyzer, business docs, EDI validator, and website analyzer. Beat NotebookLM and ChatPDF.",
                         meta_keywords="AI PDF reader, document AI, PDF analysis, resume analyzer, ATS score, EDI validator, workflow AI")

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

# New pages
@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html",
                         page_title="About AI Document Chatbot - AIGPT Technologies",
                         meta_description="Learn about AI Document Chatbot built by AIGPT Technologies. AI-powered PDF analysis, Q&A, text extraction, and more.",
                         meta_keywords="AI PDF reader, document AI, PDF analysis, AIGPT Technologies")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.get_json()
        # In production, you'd send an email here
        return jsonify({"success": True, "message": "Thank you for contacting us! We'll get back to you soon."})
    return render_template("contact.html",
                         page_title="Contact Us - AIGPT Technologies",
                         meta_description="Contact AIGPT Technologies for AI chatbots, automation tools, web development, and Navis TOS services.",
                         meta_keywords="contact AIGPT, AI chatbot services, automation tools")

# Tool pages
@app.route("/tools/pdf-summary", methods=["GET"])
def tool_pdf_summary():
    return render_template("tool.html",
                         tool_slug="pdf-summary",
                         tool_name="PDF Summary AI",
                         tool_description="AI-powered PDF summarization tool",
                         page_title="PDF Summary AI - AI Document Chatbot",
                         meta_description="AI-powered PDF summarization tool",
                         meta_keywords="AI PDF reader, PDF summary, document AI, PDF analysis")

@app.route("/tools/invoice-reader", methods=["GET"])
def tool_invoice_reader():
    return render_template("tool.html",
                         tool_slug="invoice-reader",
                         tool_name="Invoice Reader AI",
                         tool_description="Extract and analyze invoice data with AI",
                         page_title="Invoice Reader AI - AI Document Chatbot",
                         meta_description="Extract and analyze invoice data with AI",
                         meta_keywords="AI PDF reader, invoice reader, document AI, PDF analysis")

@app.route("/tools/contract-analyzer", methods=["GET"])
def tool_contract_analyzer():
    return render_template("tool.html",
                         tool_slug="contract-analyzer",
                         tool_name="Contract Analyzer AI",
                         tool_description="Analyze contracts and legal documents with AI",
                         page_title="Contract Analyzer AI - AI Document Chatbot",
                         meta_description="Analyze contracts and legal documents with AI",
                         meta_keywords="AI PDF reader, contract analyzer, document AI, PDF analysis")

@app.route("/tools/salary-slip-analyzer", methods=["GET"])
def tool_salary_slip():
    return render_template("tool.html",
                         tool_slug="salary-slip-analyzer",
                         tool_name="Salary Slip Analyzer",
                         tool_description="Analyze salary slips and payroll documents",
                         page_title="Salary Slip Analyzer - AI Document Chatbot",
                         meta_description="Analyze salary slips and payroll documents",
                         meta_keywords="AI PDF reader, salary slip analyzer, document AI, PDF analysis")

@app.route("/tools/resume-analyzer", methods=["GET"])
def tool_resume_analyzer():
    return render_template("tool.html",
                         tool_slug="resume-analyzer",
                         tool_name="Resume Analyzer AI",
                         tool_description="Analyze resumes and CVs with AI",
                         page_title="Resume Analyzer AI - AI Document Chatbot",
                         meta_description="Analyze resumes and CVs with AI",
                         meta_keywords="AI PDF reader, resume analyzer, document AI, PDF analysis")

@app.route("/tools/website-summary", methods=["GET"])
def tool_website_summary():
    return render_template("tool.html",
                         tool_slug="website-summary",
                         tool_name="Website-to-Summary AI",
                         tool_description="Convert websites into summaries with AI",
                         page_title="Website-to-Summary AI - AI Document Chatbot",
                         meta_description="Convert websites into summaries with AI",
                         meta_keywords="AI PDF reader, website summary, document AI, PDF analysis")

# Share and export endpoints
@app.route("/share/<share_id>", methods=["GET"])
def share_page(share_id):
    chat_data = chat_history_store.get(share_id)
    if not chat_data:
        return render_template("404.html"), 404
    return render_template("share.html", chat_data=chat_data, share_id=share_id)

@app.route("/api/save-chat", methods=["POST"])
def save_chat():
    data = request.get_json()
    share_id = str(uuid.uuid4())[:8]
    chat_history_store[share_id] = {
        "messages": data.get("messages", []),
        "created_at": datetime.now().isoformat(),
        "share_id": share_id
    }
    return jsonify({"share_id": share_id, "share_url": f"/share/{share_id}"})

@app.route("/api/export-pdf", methods=["POST"])
def export_pdf():
    # In production, use a library like reportlab or weasyprint
    data = request.get_json()
    return jsonify({"message": "PDF export feature coming soon", "data": data})

# ==================== WORKFLOW ENDPOINTS ====================

@app.route("/api/workflow/extract-insights", methods=["POST"])
def workflow_extract_insights():
    """Extract insights from document"""
    try:
        data = request.get_json()
        document_type = data.get("document_type", "general")
        retriever = retriever_cache.get("active")
        
        if not retriever:
            return jsonify({"error": "Please upload a document first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if WorkflowProcessor:
            processor = WorkflowProcessor(openai_key)
            insights = processor.extract_insights(retriever, document_type)
            return jsonify(insights)
        else:
            return jsonify({"error": "WorkflowProcessor not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/workflow/action-items", methods=["POST"])
def workflow_action_items():
    """Generate action items"""
    try:
        retriever = retriever_cache.get("active")
        if not retriever:
            return jsonify({"error": "Please upload a document first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if WorkflowProcessor:
            processor = WorkflowProcessor(openai_key)
            action_items = processor.generate_action_items(retriever)
            return jsonify({"actionItems": action_items})
        else:
            return jsonify({"error": "WorkflowProcessor not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/workflow/summary", methods=["POST"])
def workflow_summary():
    """Create summary"""
    try:
        data = request.get_json()
        summary_type = data.get("type", "executive")
        retriever = retriever_cache.get("active")
        
        if not retriever:
            return jsonify({"error": "Please upload a document first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if WorkflowProcessor:
            processor = WorkflowProcessor(openai_key)
            summary = processor.create_summary(retriever, summary_type)
            return jsonify({"summary": summary})
        else:
            return jsonify({"error": "WorkflowProcessor not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/workflow/email-draft", methods=["POST"])
def workflow_email_draft():
    """Generate email draft"""
    try:
        data = request.get_json()
        email_type = data.get("type", "summary")
        retriever = retriever_cache.get("active")
        
        if not retriever:
            return jsonify({"error": "Please upload a document first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if WorkflowProcessor:
            processor = WorkflowProcessor(openai_key)
            email = processor.generate_email_draft(retriever, email_type)
            return jsonify(email)
        else:
            return jsonify({"error": "WorkflowProcessor not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/workflow/risk-analysis", methods=["POST"])
def workflow_risk_analysis():
    """Produce risk analysis"""
    try:
        retriever = retriever_cache.get("active")
        if not retriever:
            return jsonify({"error": "Please upload a document first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if WorkflowProcessor:
            processor = WorkflowProcessor(openai_key)
            risk_analysis = processor.produce_risk_analysis(retriever)
            return jsonify(risk_analysis)
        else:
            return jsonify({"error": "WorkflowProcessor not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/workflow/compare", methods=["POST"])
def workflow_compare():
    """Compare two documents"""
    try:
        data = request.get_json()
        file_id_1 = data.get("file_id_1", "active")
        file_id_2 = data.get("file_id_2")
        comparison_type = data.get("type", "general")
        
        retriever1 = retriever_cache.get(file_id_1)
        retriever2 = retriever_cache.get(file_id_2) if file_id_2 else retriever_cache.get("active")
        
        if not retriever1 or not retriever2:
            return jsonify({"error": "Please upload both documents first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if WorkflowProcessor:
            processor = WorkflowProcessor(openai_key)
            comparison = processor.compare_documents(retriever1, retriever2, comparison_type)
            return jsonify(comparison)
        else:
            return jsonify({"error": "WorkflowProcessor not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== RESUME ANALYZER ENDPOINTS ====================

@app.route("/resume-analyzer", methods=["GET"])
def resume_analyzer_page():
    return render_template("resume_analyzer_seo.html",
                         page_title="AI Resume Analyzer – Free ATS Score & JD Match | AIGPT",
                         meta_description="Analyze your resume with AI. Get ATS score, rewrite, JD match, and improvements instantly. Free resume checker with grammar fixes, skill gap analysis, and keyword optimization.",
                         meta_keywords="resume analyzer, ATS score, resume checker, JD match, resume optimization, ATS resume checker, free resume analyzer, resume AI")

@app.route("/api/resume/ats-score", methods=["POST"])
def resume_ats_score():
    """Calculate ATS score"""
    try:
        data = request.get_json()
        jd_file_id = data.get("jd_file_id")
        
        resume_retriever = retriever_cache.get("active")
        jd_retriever = retriever_cache.get(jd_file_id) if jd_file_id else None
        
        if not resume_retriever:
            return jsonify({"error": "Please upload a resume first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if ResumeAnalyzer:
            analyzer = ResumeAnalyzer(openai_key)
            ats_score = analyzer.calculate_ats_score(resume_retriever, jd_retriever)
            return jsonify(ats_score)
        else:
            return jsonify({"error": "ResumeAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resume/match-jd", methods=["POST"])
def resume_match_jd():
    """Match resume with job description"""
    try:
        data = request.get_json()
        jd_file_id = data.get("jd_file_id")
        
        resume_retriever = retriever_cache.get("active")
        jd_retriever = retriever_cache.get(jd_file_id)
        
        if not resume_retriever or not jd_retriever:
            return jsonify({"error": "Please upload both resume and job description"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if ResumeAnalyzer:
            analyzer = ResumeAnalyzer(openai_key)
            match_result = analyzer.match_with_jd(resume_retriever, jd_retriever)
            return jsonify(match_result)
        else:
            return jsonify({"error": "ResumeAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resume/rewrite", methods=["POST"])
def resume_rewrite():
    """Rewrite resume with improvements"""
    try:
        data = request.get_json()
        improvements = data.get("improvements", [])
        
        resume_retriever = retriever_cache.get("active")
        if not resume_retriever:
            return jsonify({"error": "Please upload a resume first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if ResumeAnalyzer:
            analyzer = ResumeAnalyzer(openai_key)
            rewritten = analyzer.rewrite_resume(resume_retriever, improvements)
            return jsonify({"rewrittenResume": rewritten})
        else:
            return jsonify({"error": "ResumeAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resume/full-report", methods=["POST"])
def resume_full_report():
    """Generate full resume analysis report with all enhancements"""
    try:
        data = request.get_json()
        jd_file_id = data.get("jd_file_id")
        
        resume_retriever = retriever_cache.get("active")
        jd_retriever = retriever_cache.get(jd_file_id) if jd_file_id else None
        
        if not resume_retriever:
            return jsonify({"error": "Please upload a resume first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if ResumeAnalyzer:
            analyzer = ResumeAnalyzer(openai_key)
            report = analyzer.generate_resume_report(resume_retriever, jd_retriever)
            return jsonify(report)
        else:
            return jsonify({"error": "ResumeAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resume/grammar-analysis", methods=["POST"])
def resume_grammar_analysis():
    """Analyze grammar and clarity"""
    try:
        resume_retriever = retriever_cache.get("active")
        if not resume_retriever:
            return jsonify({"error": "Please upload a resume first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if ResumeAnalyzer:
            analyzer = ResumeAnalyzer(openai_key)
            analysis = analyzer.analyze_grammar_clarity(resume_retriever)
            return jsonify(analysis)
        else:
            return jsonify({"error": "ResumeAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resume/skill-gaps", methods=["POST"])
def resume_skill_gaps():
    """Analyze skill gaps"""
    try:
        data = request.get_json()
        jd_file_id = data.get("jd_file_id")
        
        resume_retriever = retriever_cache.get("active")
        jd_retriever = retriever_cache.get(jd_file_id)
        
        if not resume_retriever or not jd_retriever:
            return jsonify({"error": "Please upload both resume and job description"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if ResumeAnalyzer:
            analyzer = ResumeAnalyzer(openai_key)
            gaps = analyzer.analyze_skill_gaps(resume_retriever, jd_retriever)
            return jsonify(gaps)
        else:
            return jsonify({"error": "ResumeAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resume/keyword-optimization", methods=["POST"])
def resume_keyword_optimization():
    """Optimize keywords"""
    try:
        data = request.get_json()
        jd_file_id = data.get("jd_file_id")
        
        resume_retriever = retriever_cache.get("active")
        jd_retriever = retriever_cache.get(jd_file_id) if jd_file_id else None
        
        if not resume_retriever:
            return jsonify({"error": "Please upload a resume first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if ResumeAnalyzer:
            analyzer = ResumeAnalyzer(openai_key)
            optimization = analyzer.optimize_keywords(resume_retriever, jd_retriever)
            return jsonify(optimization)
        else:
            return jsonify({"error": "ResumeAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== EDI ANALYZER ENDPOINTS ====================

@app.route("/edi-validator", methods=["GET"])
def edi_validator_page():
    return render_template("edi_validator_seo.html",
                         page_title="EDI Validator – BAPLIE, MOVINS, COPRAR File Analyzer | AIGPT",
                         meta_description="Validate BAPLIE, MOVINS, COPRAR container EDI files. Detect errors and summarize cargo instantly. Support for IFTMIN, CODECO, CUSCAR formats.",
                         meta_keywords="EDI validator, BAPLIE, MOVINS, COPRAR, EDI analyzer, logistics EDI, container EDI, EDI validation")

@app.route("/business-docs-ai", methods=["GET"])
def business_docs_page():
    return render_template("business_docs.html",
                         page_title="AI Business Document Analyzer – Invoices & Contracts | AIGPT",
                         meta_description="Upload invoices, contracts, salary slips, and reports. AI finds insights, risks, and action items.",
                         meta_keywords="business document analyzer, invoice analyzer, contract analyzer, salary slip analyzer")

@app.route("/website-analyzer", methods=["GET"])
def website_analyzer_page():
    return render_template("website_analyzer.html",
                         page_title="AI Website Analyzer – SEO & Content Summary | AIGPT",
                         meta_description="Paste any URL. Get instant SEO insights, structure breakdown, and recommendations.",
                         meta_keywords="website analyzer, SEO analyzer, content analyzer, website SEO checker")

@app.route("/api/edi/analyze", methods=["POST"])
def edi_analyze():
    """Analyze EDI document"""
    try:
        retriever = retriever_cache.get("active")
        if not retriever:
            return jsonify({"error": "Please upload an EDI document first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if EDIAnalyzer:
            analyzer = EDIAnalyzer(openai_key)
            analysis = analyzer.analyze_edi(retriever)
            return jsonify(analysis)
        else:
            return jsonify({"error": "EDIAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== OUTPUT FORMAT ENDPOINTS ====================

@app.route("/api/export/json", methods=["POST"])
def export_json():
    """Export data as JSON"""
    try:
        data = request.get_json()
        if OutputGenerator:
            json_output = OutputGenerator.to_json(data.get("data", {}))
            return Response(json_output, mimetype='application/json',
                          headers={'Content-Disposition': 'attachment; filename=export.json'})
        else:
            return jsonify({"error": "OutputGenerator not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export/excel", methods=["POST"])
def export_excel():
    """Export data as Excel CSV"""
    try:
        data = request.get_json()
        if OutputGenerator:
            csv_output = OutputGenerator.to_excel_csv(data.get("data", []))
            return Response(csv_output, mimetype='text/csv',
                          headers={'Content-Disposition': 'attachment; filename=export.csv'})
        else:
            return jsonify({"error": "OutputGenerator not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export/email", methods=["POST"])
def export_email():
    """Generate email draft"""
    try:
        data = request.get_json()
        if OutputGenerator:
            email = OutputGenerator.to_email_draft(
                data.get("subject", "Document Summary"),
                data.get("body", ""),
                data.get("recipients", [])
            )
            return jsonify(email)
        else:
            return jsonify({"error": "OutputGenerator not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export/slack", methods=["POST"])
def export_slack():
    """Generate Slack message"""
    try:
        data = request.get_json()
        if OutputGenerator:
            slack_msg = OutputGenerator.to_slack_message(
                data.get("title", "Document Analysis"),
                data.get("content", ""),
                data.get("fields", [])
            )
            return jsonify(slack_msg)
        else:
            return jsonify({"error": "OutputGenerator not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export/teams", methods=["POST"])
def export_teams():
    """Generate Teams message"""
    try:
        data = request.get_json()
        if OutputGenerator:
            teams_msg = OutputGenerator.to_teams_message(
                data.get("title", "Document Analysis"),
                data.get("content", ""),
                data.get("facts", [])
            )
            return jsonify(teams_msg)
        else:
            return jsonify({"error": "OutputGenerator not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== MULTI-FILE ENDPOINTS ====================

@app.route("/api/upload-multi", methods=["POST"])
def upload_multi():
    """Upload multiple files for comparison"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files["file"]
        file_id = request.form.get("file_id", str(uuid.uuid4())[:8])
        
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        
        if not filename.endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported"}), 400
        
        text = ""
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()
        
        docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([text])
        
        openai_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        
        retriever_cache[file_id] = vectordb.as_retriever()
        file_store[file_id] = {"filename": filename, "uploaded_at": datetime.now().isoformat()}
        
        return jsonify({"message": "File uploaded successfully", "file_id": file_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== BUSINESS DOCS ENDPOINTS ====================

@app.route("/api/business-docs/analyze", methods=["POST"])
def business_docs_analyze():
    """Analyze business document"""
    try:
        retriever = retriever_cache.get("active")
        if not retriever:
            return jsonify({"error": "Please upload a document first"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if BusinessDocsAnalyzer:
            analyzer = BusinessDocsAnalyzer(openai_key)
            analysis = analyzer.analyze_business_doc(retriever)
            return jsonify(analysis)
        else:
            return jsonify({"error": "BusinessDocsAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== WEBSITE ANALYZER ENDPOINTS ====================

@app.route("/api/website/analyze", methods=["POST"])
def website_analyze():
    """Analyze website"""
    try:
        data = request.get_json()
        url = data.get("url")
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Fetch URL and create retriever
        page = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(page.text, "html.parser")
        text = soup.get_text()
        
        docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([text])
        
        openai_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        retriever = vectordb.as_retriever()
        
        if WebsiteAnalyzer:
            analyzer = WebsiteAnalyzer(openai_key)
            analysis = analyzer.full_website_analysis(url, retriever)
            return jsonify(analysis)
        else:
            return jsonify({"error": "WebsiteAnalyzer not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== DEMO ENDPOINTS ====================

@app.route("/api/demo/resume", methods=["GET"])
def demo_resume():
    """Return demo resume data"""
    return jsonify({
        "demo": True,
        "message": "Demo resume analysis",
        "sampleData": {
            "atsScore": {"overallScore": 75},
            "strengths": ["Well-structured format", "Clear work history"],
            "weaknesses": ["Missing keywords", "Could improve bullet points"]
        }
    })

@app.route("/api/demo/business", methods=["GET"])
def demo_business():
    """Return demo business doc data"""
    return jsonify({
        "demo": True,
        "message": "Demo business document analysis",
        "sampleData": {
            "documentType": "Invoice",
            "summary": "Sample invoice analysis",
            "tables": [{"tableName": "Line Items", "rows": []}]
        }
    })

@app.route("/api/demo/edi", methods=["GET"])
def demo_edi():
    """Return demo EDI data"""
    return jsonify({
        "demo": True,
        "message": "Demo EDI analysis",
        "sampleData": {
            "formatType": "BAPLIE",
            "validation": {"isValid": True, "errors": [], "warnings": []}
        }
    })

@app.route("/api/demo/website", methods=["GET"])
def demo_website():
    """Return demo website analysis"""
    return jsonify({
        "demo": True,
        "message": "Demo website analysis",
        "sampleData": {
            "seoScore": 80,
            "keywords": ["AI", "document", "analyzer"],
            "recommendations": ["Improve meta description", "Add more H2 tags"]
        }
    })

@app.route("/styles.css", methods=["GET"])
def serve_css():
    return send_from_directory(".", "styles.css")

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        if not filename.endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported"}), 400

        text = ""
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()

        docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([text])

        openai_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        retriever_cache["active"] = vectordb.as_retriever()

        return jsonify({"message": "✅ File uploaded and processed successfully."})

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/fetch-url", methods=["POST"])
def fetch_url():
    try:
        url = request.get_json().get("url")
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        text = soup.get_text()

        docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([text])

        openai_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        retriever_cache["active"] = vectordb.as_retriever()

        return jsonify({"message": "✅ Website content fetched and processed."})

    except Exception as e:
        print(f"❌ URL Fetch error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    try:
        query = request.json.get("question")
        retriever = retriever_cache.get("active")
        if not retriever:
            return jsonify({"error": "Please upload a file or fetch a website first."}), 400

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured. Please set it in Railway environment variables."}), 500

        # Use modern LangChain LCEL approach
        llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)
        
        # Create a prompt template
        template = """Use the following pieces of context to answer the question. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}

Question: {question}

Answer:"""
        
        prompt = PromptTemplate.from_template(template)
        
        # Create the chain using LCEL
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        # Invoke the chain
        answer = chain.invoke(query)
        
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"❌ Ask error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
