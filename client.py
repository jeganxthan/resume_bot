import sys
import socketio
import requests
import jwt

API_URL = "http://localhost:5000/api/auth"

if len(sys.argv) != 3:
    print("Usage: python client.py <email> <password>")
    sys.exit(1)

email = sys.argv[1]
password = sys.argv[2]

# Step 1 — Login to get JWT
resp = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
if resp.status_code != 200:
    print("❌ Login failed:", resp.json())
    sys.exit(1)

access_token = resp.json()["access_token"]
print("✅ Logged in successfully. JWT obtained.")

# Decode JWT to get sender_id
decoded_token = jwt.decode(access_token, options={"verify_signature": False})
sender_id = decoded_token.get("sub")
print(f"🔑 Sender ID: {sender_id}")

# Step 2 — Connect to Socket.IO with JWT
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to socket server")


@sio.on("connected")
def on_connected(data):
    print("🔗", data["message"])


@sio.on("private_message")
def on_private_message(data):
    print(f"📩 Message from {data['sender_id']}: {data['content']}")


@sio.on("error")
def on_error(data):
    print("⚠ Error:", data.get("message"))


@sio.event
def disconnect():
    print("❌ Disconnected from server")


print("Connecting to socket server...")
sio.connect(
    "http://localhost:5000",
    transports=["websocket"],
    auth={"token": access_token}
)

# Step 3 — Interactive message sending
try:
    while True:
        to_id = input("Send to (user_id): ").strip()
        msg = input("Message: ").strip()
        if not to_id or not msg:
            print("❌ Invalid input")
            continue

        sio.emit("private_message", {
            "token": access_token,  # let server decode sender_id
            "to": int(to_id),
            "message": msg
        })

except KeyboardInterrupt:
    print("\n💬 Chat ended")
    sio.disconnect()
