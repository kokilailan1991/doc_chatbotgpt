import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from dotenv import load_dotenv

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA

# Load API key from .env
load_dotenv()

app = Flask(__name__, static_url_path="", static_folder=".")
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

retriever_cache = {}

@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(".", "index.html")

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

        # Read PDF
        text = ""
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()

        # Split text
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.create_documents([text])

        # Embed and store
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise Exception("OPENAI_API_KEY not found in environment!")

        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        vectordb = FAISS.from_documents(docs, embeddings)
        retriever = vectordb.as_retriever()
        retriever_cache["active"] = retriever

        return jsonify({"message": "✅ File uploaded and processed successfully."})

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    try:
        query = request.json.get("question")
        retriever = retriever_cache.get("active")
        if not retriever:
            return jsonify({"error": "Please upload a file first."}), 400

        qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY")),
            chain_type="stuff",
            retriever=retriever
        )
        result = qa.run(query)
        return jsonify({"answer": result})

    except Exception as e:
        print(f"❌ Ask error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
