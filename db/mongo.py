from pymongo import MongoClient
from config.config import MONGO_URI
import certifi

def _connect():
    # Try WITHOUT tlsCAFile first — newer pymongo handles certs internally,
    # and certifi.where() can sometimes conflict with the container's OpenSSL.
    try:
        c = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=20000,
            connectTimeoutMS=20000,
            retryWrites=True,
        )
        c.admin.command("ping")
        print("✅ MongoDB connected (no tlsCAFile)")
        return c
    except Exception as e1:
        print(f"⚠️  Connection without tlsCAFile failed: {e1}")

    # Fallback: explicit certifi CA bundle
    try:
        c = MongoClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=20000,
            connectTimeoutMS=20000,
            retryWrites=True,
        )
        c.admin.command("ping")
        print("✅ MongoDB connected (with tlsCAFile)")
        return c
    except Exception as e2:
        print(f"❌ Connection with tlsCAFile also failed: {e2}")
        raise

client = _connect()

db = client["meeting_ai"]

user_collection = db["users"]
token_collection = db["tokens"]
meeting_collection = db["meetings"]
chat_collection = db["chats"]
report_collection = db["reports"]
