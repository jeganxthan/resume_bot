from dotenv import load_dotenv
load_dotenv()
import os, uuid, json, requests
from flask import Blueprint, request, jsonify
from models.models import Resume
from db import db
from flask_jwt_extended import jwt_required  
from config.resume_utils import extract_text, extract_resume_json

gemini_bp = Blueprint("gemini", __name__, url_prefix="/gemini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY not found in environment variables")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
HEADERS = {"Content-Type": "application/json"}

GEMINI_GREETINGS = ["hi", "hello", "hey", "how are you", "good morning", "good evening"]

@gemini_bp.route("/upload_resume", methods=["POST"])
@jwt_required()
def upload_resume():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join("data/uploads", filename)
        os.makedirs("data/uploads", exist_ok=True)
        file.save(filepath)

        text = extract_text(filepath)

        resume_json = extract_resume_json(text)
        
        os.remove(filepath)

    except Exception as e:
        return jsonify({"error": "Failed to process resume", "details": str(e)}), 400

    api_key = str(uuid.uuid4())

    resume = Resume(api_key=api_key, resume_json=resume_json)
    db.session.add(resume)
    db.session.commit()

    return jsonify({"message": "Resume uploaded and processed successfully", "x-api-key": api_key})

@gemini_bp.route("/ask", methods=["POST"])
@jwt_required()
def ask_resume():
    api_key = request.headers.get("x-api-key")
    question = request.json.get("question")

    if not api_key or not question:
        return jsonify({"error": "Missing x-api-key or question"}), 400

    q_lower = question.strip().lower()
    if q_lower in GEMINI_GREETINGS:
        if q_lower in ["hi", "hello", "hey"]:
            return jsonify({"answer": "Hello! 👋"})
        elif "how are you" in q_lower:
            return jsonify({"answer": "I'm doing great, thanks for asking! How about you?"})
        elif "good morning" in q_lower:
            return jsonify({"answer": "Good morning! ☀️ Hope you have a great day ahead."})
        elif "good evening" in q_lower:
            return jsonify({"answer": "Good evening! 🌙 How’s your day going?"})

    resume = Resume.query.filter_by(api_key=api_key).first()
    if not resume:
        return jsonify({"error": "Invalid x-api-key"}), 403

    prompt = {
        "contents": [{
            "parts": [{
                "text": f"""
You are a resume assistant AI.
Only answer questions using this candidate's resume JSON:
{json.dumps(resume.resume_json, indent=2)}

Question: {question}
"""
            }]
        }]
    }

    response = requests.post(GEMINI_URL, headers=HEADERS, data=json.dumps(prompt))

    if response.status_code == 200:
        result = response.json()
        answer = result["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"answer": answer})
    else:
        return jsonify({"error": response.text}), response.status_code
