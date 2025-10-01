import eventlet
eventlet.monkey_patch()  # Must be first

from flask_socketio import SocketIO, emit
from flask_jwt_extended import decode_token, get_jwt_identity
from flask import request, current_app
from db import db
from models.message import Message
from models.auth import User

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")

connected_users = {}  


@socketio.on("connect")
def handle_connect(auth):
    with current_app.app_context():
        token = auth.get("token") if auth else None
        if not token:
            print("❌ No token provided")
            return False

        try:
            decoded = decode_token(token)
            user_id = int(decoded["sub"])
            user = User.query.get(user_id)

            if not user:
                print(f"❌ User not found for id: {user_id}")
                return False

            connected_users[user_id] = request.sid
            emit("connected", {"message": f"User {user.username} connected"})
            print(f"✅ User {user.username} connected with sid {request.sid}")

        except Exception as e:
            print("⚠ JWT error:", e)
            return False


@socketio.on("private_message")
def handle_private_message(data):
    with current_app.app_context():
        sender_id = None
        try:
            token = request.args.get("token") or data.get("token")
            if token:
                decoded = decode_token(token)
                sender_id = int(decoded["sub"])
        except Exception as e:
            emit("error", {"message": "Invalid sender token"})
            return

        recipient_id = data.get("to")
        message = data.get("message")

        if not sender_id or not recipient_id or not message:
            emit("error", {"message": "Invalid message data"})
            return

        new_message = Message(sender_id=sender_id, recipient_id=recipient_id, content=message)
        db.session.add(new_message)
        db.session.commit()

        if recipient_id in connected_users:
            recipient_sid = connected_users[recipient_id]
            emit("private_message", new_message.to_dict(), room=recipient_sid)
            print(f"📩 {sender_id} -> {recipient_id}: {message}")
        else:
            emit("error", {"message": f"User {recipient_id} not connected"}, room=request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    with current_app.app_context():
        for user_id, sid in list(connected_users.items()):
            if sid == request.sid:
                print(f"❌ User disconnected: {user_id}")
                del connected_users[user_id]
                break
