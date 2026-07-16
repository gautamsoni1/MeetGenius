import os

# 🔥 ADD THIS LINE HERE (TOP)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI is missing from environment variables")

RECALL_API_KEY = os.getenv("RECALL_API_KEY")
BASE_URL       = os.getenv("BASE_URL", "https://us-west-2.recall.ai/api/v1")

# Public backend URL (Render service URL, no trailing slash)
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
WEBHOOK_URL = f"{BACKEND_URL}/webhook" if BACKEND_URL else ""
RECORD_API = f"{BACKEND_URL}/record"
# ==============================
# 🔹 ASSEMBLYAI CONFIG
# ==============================
ASSEMBLY_API_KEY       = os.getenv("ASSEMBLY_API_KEY")
ASSEMBLY_UPLOAD_URL    = os.getenv("ASSEMBLY_UPLOAD_URL")
ASSEMBLY_TRANSCRIPT_URL = os.getenv("ASSEMBLY_TRANSCRIPT_URL")

# ==============================
# 🔹 GROQ CONFIG
# ==============================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# SCOPES = ["https://www.googleapis.com/auth/calendar"]
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


# ==============================
# 🔹 HEADER HELPERS
# ==============================
def get_assembly_headers():
    if not ASSEMBLY_API_KEY:
        raise RuntimeError("❌ ASSEMBLY_API_KEY is missing")
    return {"authorization": ASSEMBLY_API_KEY}

# ==============================
# 🔹 STORAGE PATHS
# ==============================
# recordings/ lives at project root: <project_root>/recordings/
RECORDINGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "recordings"
)

os.makedirs(RECORDINGS_DIR, exist_ok=True)

# ==============================
# 🔹 VALIDATION
# ==============================
if not RECALL_API_KEY:
    raise RuntimeError("❌ RECALL_API_KEY is missing from .env")

if not BACKEND_URL:
    print("⚠️  BACKEND_URL is not set — webhook and record trigger URLs will not work!")

# ==============================
# 🔹 STARTUP DEBUG PRINTS
# ==============================
print("🌐 BACKEND_URL    :", BACKEND_URL)
print("🔗 WEBHOOK_URL    :", WEBHOOK_URL)
print("📁 RECORDINGS_DIR :", RECORDINGS_DIR)
print("Recall ai :",RECALL_API_KEY)
