📄 Resume AI Assistant (Flask + Gemini + JWT + Socket.IO)
🚀 Overview

This project is a resume assistant web service built using Flask, Postgres, JWT authentication, and Socket.IO.

Features:
Upload resumes (PDF, DOCX, TXT)
Parse and extract structured data (name, email, phone, skills, etc.)
Store structured JSON in the database (Postgres)
Use Google Gemini API to answer resume-related questions
JWT authentication for secure API access
Real-time chat system using Flask-SocketIO

🛠️ Tech Stack

Backend: Flask, Flask-JWT-Extended, Flask-SocketIO

Database: PostgreSQL + SQLAlchemy ORM

Resume Parsing: PyPDF2, python-docx, regex

AI: Google Gemini API (Generative Language)

Auth: JWT Tokens

Real-time: WebSocket (via Socket.IO + Eventlet)
