from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os
from werkzeug.utils import secure_filename
from config.otp_utility import generate_otp
from models.auth import User
from db import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.otp import OTP
import datetime
from config.email_service import send_otp_email

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(upload_folder, filename)

# ---------------- Register ----------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not password or not email:
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    otp_code = generate_otp(new_user.id)
    send_otp_email(new_user.email, otp_code)

    return jsonify({"message": "User registered successfully. OTP has been sent to your email."}), 201


# ---------------- Login ----------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token}), 200


# ---------------- Upload Profile Image ----------------
@auth_bp.route('/profileImage', methods=['POST'])
@jwt_required()
def upload_image():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Save only the filename in DB
        user.profile_image = filename
        db.session.commit()

        # Return URL for frontend
        file_url = f"{request.host_url}api/auth/uploads/{filename}"
        return jsonify({"message": "Image uploaded successfully", "url": file_url}), 200

    return jsonify({"error": "File type not allowed"}), 400


# ---------------- Profile ----------------
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    file_url = f"{request.host_url}api/auth/uploads/{user.profile_image}" if user.profile_image else None

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "profile_image": file_url
    }), 200
# ---------------- Request OTP ----------------
@auth_bp.route('/request-otp', methods=['POST'])
def request_otp():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp_code = generate_otp(user.id)
    send_otp_email(user.email, otp_code)

    return jsonify({"message": "OTP sent successfully"}), 200


# ---------------- Verify OTP ----------------
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    code = data.get("otp")

    if not email or not code:
        return jsonify({"error": "Email and OTP are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp = OTP.query.filter_by(user_id=user.id, code=code).first()
    if not otp:
        return jsonify({"error": "Invalid OTP"}), 400

    if otp.expires_at < datetime.datetime.utcnow():
        db.session.delete(otp)
        db.session.commit()
        return jsonify({"error": "OTP expired"}), 400

    db.session.delete(otp)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token}), 200
