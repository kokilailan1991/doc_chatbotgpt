import os
import sys

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import Flask and basic dependencies
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import json
from datetime import datetime

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

@app.route("/", methods=["GET"])
def serve_index():
    return render_template("index.html", 
                         page_title="AI Document Chatbot - Analyze PDFs with AI",
                         meta_description="AI-powered chatbot to analyze and answer questions from PDF documents. Upload PDFs, ask questions, and get instant AI-powered answers.",
                         meta_keywords="AI PDF reader, document AI, PDF analysis, PDF chatbot, document analysis")

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
