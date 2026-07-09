import os
import uuid
from datetime import datetime

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config.config import SCOPES, GOOGLE_REDIRECT_URI
from auth.token_service import save_token
from db.mongo import user_collection

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

flow_store = {}


from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Render secret files land in /etc/secrets/ — check there first,
# fall back to local credentials/ folder for local development.
_RENDER_SECRET_PATH = Path("/etc/secrets/client_secrets.json")
_LOCAL_SECRET_PATH = BASE_DIR / "credentials" / "client_secrets.json"

CLIENT_SECRET_FILE = _RENDER_SECRET_PATH if _RENDER_SECRET_PATH.exists() else _LOCAL_SECRET_PATH

def create_flow():
    print("Using:", CLIENT_SECRET_FILE)

    return Flow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )


# =========================
# LOGIN
# =========================
def get_auth_url():
    flow = create_flow()

    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )

    flow_store[state] = flow

    print("🔥 LOGIN STATE:", state)

    return auth_url


# =========================
# CALLBACK (FIXED - NO LOOP)
# =========================
def handle_callback(full_url: str, state: str):
    if state not in flow_store:
        return {"error": "Session expired. Please login again"}

    flow = flow_store.pop(state)  # pop immediately — burn the state either way

    # exchange code
    try:
        flow.fetch_token(authorization_response=full_url)
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        return {"error": "Login failed or link already used. Please login again."}

    creds = flow.credentials

    try:
        service = build("oauth2", "v2", credentials=creds)
        user_info = service.userinfo().get().execute()
        email = user_info.get("email")

        user = user_collection.find_one({"email": email})

        if user:
            user_id = user["user_id"]
        else:
            user_id = str(uuid.uuid4())
            user_collection.insert_one({
                "user_id": user_id,
                "email": email,
                "created_at": datetime.utcnow()
            })

        token_data = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "email": email
        }
        save_token(user_id, token_data)

        print("✅ LOGIN SUCCESS:", email)

        return {
            "message": "Login successful",
            "user_id": user_id,
            "email": email
        }

    except Exception as e:
        print(f"❌ Post-token-exchange step failed: {e}")
        # Google login worked, but we couldn't save it — be honest about that
        return {
            "error": "Google login succeeded but saving your session failed (database issue). Please try again."
        }
