# import requests
# import webbrowser
# from http.server import BaseHTTPRequestHandler, HTTPServer
# import urllib.parse
# import threading
# import os
# from dotenv import load_dotenv
# import time

# load_dotenv()

# BASE_URL = os.getenv("NGROK_URL")

# if not BASE_URL:
#     raise Exception("NGROK_URL not found in .env")

# API_URL = f"{BASE_URL}/chat"
# LOGIN_URL = f"{BASE_URL}/auth/login"

# user_id = None


# class Handler(BaseHTTPRequestHandler):
#     def do_GET(self):
#         global user_id

#         params = urllib.parse.parse_qs(
#             urllib.parse.urlparse(self.path).query
#         )

#         user_id = params.get("user_id", [None])[0]

#         self.send_response(200)
#         self.end_headers()
#         self.wfile.write(b"Login successful! Close this tab.")


# def start_server():
#     HTTPServer(("localhost", 5000), Handler).handle_request()


# print("🔐 Opening login...")

# threading.Thread(target=start_server, daemon=True).start()

# # ✅ SIMPLE LOGIN
# webbrowser.open(LOGIN_URL)

# # wait
# while user_id is None:
#     time.sleep(1)

# print(f"✅ Logged in! User ID: {user_id}")

# # CHAT
# while True:
#     msg = input("You: ")

#     if msg.lower() == "exit":
#         break

#     res = requests.post(
#         API_URL,
#         json={
#             "user_id": user_id,
#             "message": msg
#         }
#     )

#     print("Bot:", res.json())




import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

BASE_URL = os.getenv("NGROK_URL")
API_URL = f"{BASE_URL}/chat"
LOGIN_URL = f"{BASE_URL}/auth/login"

print("🔐 Opening login...")

# open browser
import webbrowser
webbrowser.open(LOGIN_URL)

# wait for manual copy (IMPORTANT FIX)
print("\n👉 After login, copy user_id from browser response")
user_id = input("Enter user_id: ").strip()

print(f"✅ Logged in! User ID: {user_id}")

while True:
    msg = input("You: ")

    if msg.lower() == "exit":
        break

    try:
        res = requests.post(
            API_URL,
            json={
                "user_id": user_id,
                "message": msg
            },
            timeout=3000
        )

        print("Bot:", res.json())

    except Exception as e:
        print("❌ Error:", e)