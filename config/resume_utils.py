# resume_utils.py
import os
import re
import json
from docx import Document
from PyPDF2 import PdfReader

def extract_text(file_path):
    """
    Extract text from PDF, DOCX, or TXT files.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError("Unsupported file format. Use PDF, DOCX, or TXT.")

def extract_text_from_pdf(file_path):
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_resume_json(text):
    """
    Convert raw text into a structured JSON format.
    This is a simple example; you can enhance it using NLP.
    """
    resume = {}

    # Name (assumes first line is name)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    resume["name"] = lines[0] if lines else "Unknown"

    # Extract email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    resume["email"] = email_match.group(0) if email_match else ""

    # Extract phone number (simple)
    phone_match = re.search(r"(\+?\d{10,15})", text.replace(" ", ""))
    resume["phone"] = phone_match.group(0) if phone_match else ""

    # Experience, Education, Skills (very basic placeholders)
    resume["education"] = extract_section(text, ["education", "academic"])
    resume["experience"] = extract_section(text, ["experience", "work"])
    resume["skills"] = extract_section(text, ["skills", "technical"])

    return resume

def extract_section(text, keywords):
    """
    Extract text after a keyword until the next blank line.
    Very simple; can be replaced with NLP-based extraction.
    """
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            start = text_lower.find(keyword)
            section_text = text[start:]
            section_lines = [line.strip() for line in section_text.splitlines() if line.strip()]
            # return first 5 lines after keyword as example
            return section_lines[1:6]
    return []
