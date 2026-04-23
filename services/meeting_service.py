# import os
# import re
# import uuid
# import datetime

# from state.chat_state import get_state
# from db.mongo import meeting_collection


# # =========================
# # ✅ SAFE DATETIME PARSER
# # =========================
# def parse_datetime_safe(date, time):
#     try:
#         return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %I:%M %p")
#     except:
#         try:
#             return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
#         except Exception as e:
#             raise Exception(f"Invalid time format: {str(e)}")


# def handle_meeting(user_id, message):

#     msg = message.lower().strip()
#     state = get_state(user_id)

#     # ======================================================
#     # 🔥 UPDATE EXISTING MEETING
#     # ======================================================
#     if state and state.get("step") == "update_existing_meeting":

#         from services.parser import parse_meeting
#         from auth.token_service import get_token
#         from googleapiclient.discovery import build
#         from google.oauth2.credentials import Credentials

#         parsed = parse_meeting(user_id, message)

#         if not parsed:
#             return {"message": "❌ Could not understand meeting", "event_id": None}

#         date = parsed.get("date")
#         time = parsed.get("time")

#         try:
#             start = parse_datetime_safe(date, time)
#         except Exception as e:
#             return {"message": str(e), "event_id": None}

#         end = start + datetime.timedelta(minutes=parsed.get("duration", 30))

#         token = get_token(user_id)
#         if not token:
#             return {"message": "❌ Google not connected", "event_id": None}

#         creds = Credentials(
#             token=token["access_token"],
#             refresh_token=token["refresh_token"],
#             token_uri="https://oauth2.googleapis.com/token",
#             client_id=token["client_id"],
#             client_secret=token["client_secret"]
#         )

#         service = build("calendar", "v3", credentials=creds)

#         event_id = state.get("event_id")

#         event = service.events().patch(
#             calendarId="primary",
#             eventId=event_id,
#             body={
#                 "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
#                 "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"}
#             }
#         ).execute()

#         meeting_url = event.get("hangoutLink")

#         meeting_collection.update_one(
#             {"event_id": event_id},
#             {"$set": {"date": date, "time": time}}
#         )

#         return {
#             "message": f"🔄 Meeting updated successfully\n👉 {meeting_url}",
#             "meeting_url": meeting_url,
#             "event_id": event_id
#         }

#     # ======================================================
#     # 🔥 CREATE NEW MEETING
#     # ======================================================
#     if "meeting" in msg:

#         from services.parser import parse_meeting
#         from auth.token_service import get_token
#         from googleapiclient.discovery import build
#         from google.oauth2.credentials import Credentials

#         parsed = parse_meeting(user_id, message)

#         if not parsed:
#             return {"message": "❌ Could not understand meeting", "event_id": None}

#         date = parsed.get("date")
#         time = parsed.get("time")

#         try:
#             start = parse_datetime_safe(date, time)
#         except Exception as e:
#             return {"message": str(e), "event_id": None}

#         end = start + datetime.timedelta(minutes=parsed.get("duration", 30))

#         token = get_token(user_id)
#         if not token:
#             return {"message": "❌ Google not connected", "event_id": None}

#         creds = Credentials(
#             token=token["access_token"],
#             refresh_token=token["refresh_token"],
#             token_uri="https://oauth2.googleapis.com/token",
#             client_id=token["client_id"],
#             client_secret=token["client_secret"]
#         )

#         service = build("calendar", "v3", credentials=creds)

#         event = service.events().insert(
#             calendarId="primary",
#             body={
#                 "summary": parsed.get("title", "Meeting"),
#                 "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
#                 "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
#                 "conferenceData": {
#                     "createRequest": {
#                         "requestId": str(uuid.uuid4()),
#                         "conferenceSolutionKey": {"type": "hangoutsMeet"}
#                     }
#                 }
#             },
#             conferenceDataVersion=1
#         ).execute()

#         meeting_url = event.get("hangoutLink")
#         event_id = event.get("id")

#         meeting_collection.insert_one({
#             "user_id": user_id,
#             "event_id": event_id,
#             "meeting_url": meeting_url,
#             "date": date,
#             "time": time,
#             "created_at": datetime.datetime.utcnow()
#         })

#         return {
#             "message": f"📅 Meeting created\n👉 {meeting_url}",
#             "meeting_url": meeting_url,
#             "event_id": event_id
#         }

#     return {"message": "❓ Try: 'schedule meeting today 7pm'", "event_id": None}







import os
import re
import uuid
import datetime

from state.chat_state import get_state
from db.mongo import meeting_collection
from auth.token_service import get_token
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# =========================
# SAFE PARSE (AM/PM + 24h)
# =========================
def parse_datetime(date, time):
    try:
        time = re.sub(r"\s+", " ", time).strip()

        if "AM" in time or "PM" in time:
            return datetime.datetime.strptime(
                f"{date} {time}",
                "%Y-%m-%d %I:%M %p"
            )
        else:
            return datetime.datetime.strptime(
                f"{date} {time}",
                "%Y-%m-%d %H:%M"
            )
    except:
        return None


# =========================
# MAIN MEETING HANDLER
# =========================
def handle_meeting(user_id, message):

    msg = message.lower().strip()
    state = get_state(user_id)

    # ======================================================
    # 🔥 UPDATE EXISTING MEETING (PATCH - FIXED)
    # ======================================================
    if state and state.get("step") == "meeting_reconfirm":
    
        event_id = state.get("event_id")
    
        if not event_id:
            return {"message": "❌ event_id missing in state"}
    
        parsed = state.get("new_meeting")
    
        if not parsed:
            return {"message": "❌ Missing meeting data"}
    
        start = parse_datetime(parsed["date"], parsed["time"])
    
        if not start:
            return {"message": "❌ Invalid datetime"}
    
        end = start + datetime.timedelta(minutes=30)
    
        token = get_token(user_id)
    
        if not token:
            return {"message": "❌ Google not connected"}
    
        creds = Credentials(
            token=token["access_token"],
            refresh_token=token["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token["client_id"],
            client_secret=token["client_secret"]
        )
    
        service = build("calendar", "v3", credentials=creds)
    
        # 🔥 SAFE PATCH CALL
        service.events().patch(
            calendarId="primary",
            eventId=event_id,
            body={
                "start": {
                    "dateTime": start.isoformat(),
                    "timeZone": "Asia/Kolkata"
                },
                "end": {
                    "dateTime": end.isoformat(),
                    "timeZone": "Asia/Kolkata"
                }
            }
        ).execute()
    
        meeting = meeting_collection.find_one({"event_id": event_id})
    
        return {
            "message": "🔄 Meeting updated successfully",
            "meeting_url": meeting.get("meeting_url"),
            "event_id": event_id
        }

    # ======================================================
    # 🔥 CREATE NEW MEETING
    # ======================================================
    if "meeting" in msg:

        parsed = state.get("new_meeting") if state and "new_meeting" in state else None

        if not parsed:
            return {"message": "❌ Could not parse meeting"}

        start = parse_datetime(parsed["date"], parsed["time"])
        if not start:
            return {"message": "❌ Invalid time format"}

        end = start + datetime.timedelta(minutes=30)

        token = get_token(user_id)
        if not token:
            return {"message": "❌ Google not connected"}

        creds = Credentials(
            token=token["access_token"],
            refresh_token=token["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token["client_id"],
            client_secret=token["client_secret"]
        )

        service = build("calendar", "v3", credentials=creds)

        # =========================
        # CREATE EVENT (ONLY ONCE)
        # =========================
        event = service.events().insert(
            calendarId="primary",
            body={
                "summary": parsed.get("title", "Meeting"),
                "start": {
                    "dateTime": start.isoformat(),
                    "timeZone": "Asia/Kolkata"
                },
                "end": {
                    "dateTime": end.isoformat(),
                    "timeZone": "Asia/Kolkata"
                },
                "conferenceData": {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {
                            "type": "hangoutsMeet"
                        }
                    }
                }
            },
            conferenceDataVersion=1
        ).execute()

        meeting_url = event.get("hangoutLink")
        event_id = event.get("id")

        meeting_collection.insert_one({
            "user_id": user_id,
            "event_id": event_id,
            "meeting_url": meeting_url,
            "date": parsed["date"],
            "time": parsed["time"],
            "created_at": datetime.datetime.utcnow()
        })

        return {
            "message": "📅 Meeting created",
            "meeting_url": meeting_url,
            "event_id": event_id
        }

    # ======================================================
    # DEFAULT
    # ======================================================
    return {"message": "❌ No meeting action detected"}