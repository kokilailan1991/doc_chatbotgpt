import os
import sys

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import Flask and basic dependencies
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import other dependencies with error handling
try:
    import fitz  # PyMuPDF
    import requests
    from bs4 import BeautifulSoup
    
    # LangChain imports
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import CharacterTextSplitter
    from langchain.chains import RetrievalQA
except ImportError as e:
    print(f"❌ Import error: {e}", file=sys.stderr)
    print("Please ensure all dependencies are installed.", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__, static_url_path="", static_folder=".")
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

retriever_cache = {}

@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

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

        qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY")),
            chain_type="stuff",
            retriever=retriever
        )

        result = qa.invoke(query)
        return jsonify({"answer": result})

    except Exception as e:
        print(f"❌ Ask error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
