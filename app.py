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

# Tool pages - Updated routes
@app.route("/pdf-summary", methods=["GET"])
def pdf_summary_page():
    return render_template("pdf_summary.html",
                         page_title="PDF Summary AI – Free AI Document Summarizer | AIGPT",
                         meta_description="Upload any PDF and get instant AI-powered summary, key insights, risks, and action items. Free PDF analyzer with no login required.",
                         meta_keywords="PDF summary, AI PDF analyzer, document summarizer, PDF insights, PDF risk analysis")

@app.route("/tools/pdf-summary", methods=["GET"])
def tool_pdf_summary():
    return pdf_summary_page()

@app.route("/invoice-reader", methods=["GET"])
def invoice_reader_page():
    return render_template("invoice_reader.html",
                         page_title="Invoice Reader AI – Free AI Invoice Extractor | AIGPT",
                         meta_description="Extract invoice data automatically: items, quantities, prices, taxes, totals. Export to CSV. Free invoice analyzer with AI.",
                         meta_keywords="invoice reader, invoice extractor, invoice OCR, invoice analyzer, invoice parser, AI invoice")

@app.route("/tools/invoice-reader", methods=["GET"])
def tool_invoice_reader():
    return invoice_reader_page()

@app.route("/contract-analyzer", methods=["GET"])
def contract_analyzer_page():
    return render_template("contract_analyzer.html",
                         page_title="Contract Analyzer AI – Free AI Contract Review | AIGPT",
                         meta_description="Analyze contracts for clauses, obligations, risks, and missing terms. Informational only, not legal advice. Free contract analyzer.",
                         meta_keywords="contract analyzer, contract review, contract analysis, legal document analyzer, contract clauses, AI contract")

@app.route("/tools/contract-analyzer", methods=["GET"])
def tool_contract_analyzer():
    return contract_analyzer_page()

@app.route("/salary-slip", methods=["GET"])
def salary_slip_page():
    return render_template("salary_slip.html",
                         page_title="Salary Slip Analyzer – Free AI Payroll Analyzer | AIGPT",
                         meta_description="Extract payroll data: Basic, HRA, PF, deductions, net pay. Find mistakes and tax flags. Free salary slip analyzer.",
                         meta_keywords="salary slip analyzer, payroll analyzer, salary checker, payroll extractor, AI salary slip")

@app.route("/tools/salary-slip-analyzer", methods=["GET"])
def tool_salary_slip():
    return salary_slip_page()

@app.route("/tools/resume-analyzer", methods=["GET"])
def tool_resume_analyzer():
    return render_template("resume_analyzer_seo.html",
                         page_title="Resume Analyzer AI – Free ATS Score & JD Match | AIGPT",
                         meta_description="Analyze your resume with AI. Get ATS score, rewrite, JD match, and improvements instantly. Free resume checker.",
                         meta_keywords="resume analyzer, ATS score, resume checker, JD match, resume optimization")

@app.route("/website-summary", methods=["GET"])
def website_summary_page():
    return render_template("website_summary.html",
                         page_title="Website-to-Summary AI – Free Website Summarizer | AIGPT",
                         meta_description="Convert any website into a concise summary with key sections, missing content, and purpose clarity. Free website summarizer.",
                         meta_keywords="website summary, website summarizer, URL summarizer, website content extractor, AI website summary")

@app.route("/tools/website-summary", methods=["GET"])
def tool_website_summary():
    return website_summary_page()

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

@app.route("/api/analyze-edi", methods=["POST"])
def analyze_edi():
    """Analyze EDI document - NEW endpoint with proper text handling"""
    try:
        # Check if file is uploaded
        if "file" in request.files:
            file = request.files["file"]
            if file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)
                
                # Read as text if EDI file
                file_ext = filename.lower()
                is_edi_file = any(file_ext.endswith(ext) for ext in ['.edi', '.txt', '.baplie', '.movins', '.coprar'])
                
                if is_edi_file:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        edi_content = f.read()
                else:
                    return jsonify({"error": "Please upload an EDI file (.edi, .txt, .baplie, .movins, .coprar)"}), 400
            else:
                return jsonify({"error": "No file provided"}), 400
        else:
            # Try to get from cache
            retriever = retriever_cache.get("active")
            if not retriever:
                return jsonify({"error": "Please upload an EDI document first"}), 400
            
            # Extract text from retriever
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            docs = retriever.get_relevant_documents("EDI document") if hasattr(retriever, 'get_relevant_documents') else []
            edi_content = format_docs(docs) if docs else ""
            
            if not edi_content:
                return jsonify({"error": "Could not extract EDI content"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        if EDIAnalyzer:
            analyzer = EDIAnalyzer(openai_key)
            
            # Detect format and validate
            format_type = analyzer.detect_edi_format(edi_content)
            validation = analyzer.validate_structure(edi_content, format_type)
            
            # Create retriever for LLM analysis
            docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([edi_content])
            embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
            vectordb = FAISS.from_documents(docs, embeddings)
            retriever = vectordb.as_retriever()
            
            # Get full analysis
            analysis = analyzer.analyze_edi(retriever)
            
            # Enhance with validation results
            analysis["validation"] = validation
            analysis["formatType"] = format_type
            analysis["raw"] = edi_content[:1000]  # First 1000 chars for preview
            
            return jsonify(analysis)
        else:
            return jsonify({"error": "EDIAnalyzer not available"}), 500
    except Exception as e:
        print(f"❌ EDI Analyze error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/edi/analyze", methods=["POST"])
def edi_analyze():
    """Analyze EDI document - Legacy endpoint"""
    return analyze_edi()

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
        
        # Detect file type by extension
        file_ext = filename.lower()
        is_edi_file = any(file_ext.endswith(ext) for ext in ['.edi', '.txt', '.baplie', '.movins', '.coprar'])
        
        text = ""
        
        if is_edi_file:
            # Read EDI/text files as plain text
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif filename.endswith(".pdf"):
            # Read PDF files
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text()
            doc.close()
        else:
            return jsonify({"error": "Unsupported file type. Please upload PDF, EDI, or text files."}), 400
        
        if not text.strip():
            return jsonify({"error": "Could not extract text from file"}), 400
        
        docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([text])
        
        openai_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        
        retriever_cache[file_id] = vectordb.as_retriever()
        file_store[file_id] = {"filename": filename, "uploaded_at": datetime.now().isoformat(), "fileType": "edi" if is_edi_file else "pdf"}
        
        return jsonify({"message": "File uploaded successfully", "file_id": file_id, "fileType": "edi" if is_edi_file else "pdf"})
    except Exception as e:
        print(f"❌ Upload multi error: {e}")
        import traceback
        traceback.print_exc()
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

@app.route("/api/analyze-website", methods=["POST"])
def analyze_website():
    """Analyze website - Server-side endpoint to avoid CORS"""
    try:
        data = request.get_json()
        url = data.get("url")
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fetch URL server-side
        try:
            page = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }, allow_redirects=True)
            page.raise_for_status()
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Could not fetch URL: {str(e)}"}), 400
        
        soup = BeautifulSoup(page.text, "html.parser")
        
        # Extract structured data
        title = soup.find('title')
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        
        h1_tags = [h.get_text().strip() for h in soup.find_all('h1')]
        h2_tags = [h.get_text().strip() for h in soup.find_all('h2')]
        h3_tags = [h.get_text().strip() for h in soup.find_all('h3')]
        
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        images = [img.get('src') or img.get('data-src') for img in soup.find_all('img')]
        
        # Clean text content
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        text = ' '.join(text.split())  # Clean whitespace
        
        # Create retriever
        docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([text])
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500
        
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        retriever = vectordb.as_retriever()
        
        if WebsiteAnalyzer:
            analyzer = WebsiteAnalyzer(openai_key)
            
            # Prepare website data
            website_data = {
                "url": url,
                "title": title.get_text().strip() if title else "",
                "metaDescription": meta_desc.get('content', '') if meta_desc else "",
                "metaKeywords": meta_keywords.get('content', '') if meta_keywords else "",
                "h1Tags": h1_tags,
                "h2Tags": h2_tags,
                "h3Tags": h3_tags,
                "links": links[:50],
                "images": images[:20],
                "content": text[:10000],
                "html": page.text[:5000]
            }
            
            # Get full analysis
            analysis = analyzer.full_website_analysis(url, retriever)
            
            # Enhance with extracted data
            analysis["websiteData"] = website_data
            
            return jsonify(analysis)
        else:
            return jsonify({"error": "WebsiteAnalyzer not available"}), 500
    except Exception as e:
        print(f"❌ Website analyze error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/website/analyze", methods=["POST"])
def website_analyze():
    """Analyze website - Legacy endpoint"""
    return analyze_website()

# ==================== DEMO ENDPOINTS ====================

@app.route("/api/demo/resume", methods=["GET"])
def demo_resume():
    """Return demo resume data"""
    return jsonify({
        "demo": True,
        "overallScore": 82,
        "keywordScore": 20,
        "formatScore": 18,
        "skillsScore": 22,
        "experienceScore": 18,
        "educationScore": 4,
        "strengths": [
            "Well-structured format with clear sections",
            "Strong work history with quantifiable achievements",
            "Good use of action verbs",
            "Professional summary present"
        ],
        "weaknesses": [
            "Missing some industry-specific keywords",
            "Could improve bullet point formatting",
            "Skills section could be more detailed",
            "Missing certifications section"
        ],
        "recommendations": [
            "Add 5-7 more relevant keywords from job description",
            "Use more specific metrics in bullet points",
            "Include a certifications section",
            "Optimize skills section with relevant technical skills"
        ],
        "missingKeywords": ["Python", "Machine Learning", "AWS", "Docker"],
        "summary": "This resume shows strong potential with a solid foundation. The candidate has relevant experience and good formatting, but could benefit from keyword optimization and more detailed skill descriptions to improve ATS compatibility."
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
        "formatType": "BAPLIE",
        "summary": "Sample BAPLIE file containing container stowage plan for vessel MV EXAMPLE. Contains 45 containers with proper stowage positions.",
        "validation": {
            "isValid": True,
            "errors": [],
            "warnings": ["Missing weight information for 2 containers"],
            "suggestions": ["Add MEA segments for complete weight data", "Verify container numbers match physical containers"],
            "containersFound": 45,
            "containerNumbers": ["ABCD1234567", "EFGH2345678", "IJKL3456789"]
        },
        "keyFields": [
            {"name": "Vessel Name", "value": "MV EXAMPLE"},
            {"name": "Voyage", "value": "V001"},
            {"name": "Port of Loading", "value": "SINGAPORE"},
            {"name": "Port of Discharge", "value": "ROTTERDAM"}
        ],
        "parties": ["Shipping Line ABC", "Terminal Operator XYZ"],
        "locations": [
            {"type": "Origin", "code": "SGSIN", "name": "Singapore"},
            {"type": "Destination", "code": "NLRTM", "name": "Rotterdam"}
        ]
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

        # Detect file type by extension
        file_ext = filename.lower()
        is_edi_file = any(file_ext.endswith(ext) for ext in ['.edi', '.txt', '.baplie', '.movins', '.coprar'])
        
        text = ""
        
        if is_edi_file:
            # Read EDI/text files as plain text
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif filename.endswith(".pdf"):
            # Read PDF files
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text()
            doc.close()
        else:
            return jsonify({"error": "Unsupported file type. Please upload PDF, EDI, or text files."}), 400

        if not text.strip():
            return jsonify({"error": "Could not extract text from file"}), 400

        docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).create_documents([text])

        openai_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        retriever_cache["active"] = vectordb.as_retriever()

        return jsonify({"message": "✅ File uploaded and processed successfully.", "fileType": "edi" if is_edi_file else "pdf"})

    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
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
