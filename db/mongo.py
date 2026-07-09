from pymongo import MongoClient
from config.config import MONGO_URI
import certifi

client = MongoClient(
    MONGO_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=20000,
    connectTimeoutMS=20000,
    retryWrites=True,
)

db = client["meeting_ai"]

user_collection = db["users"]
token_collection = db["tokens"]
meeting_collection = db["meetings"]
chat_collection = db["chats"]
report_collection = db["reports"]
