# from fastapi import APIRouter
# from pydantic import BaseModel

# from services.meeting_service import handle_meeting
# from services.pdf_qa_service import ask_pdf, create_vector_db
# from services.email_service import send_report_to_participants
# from services.scheduler_service import add_scheduled_meeting

# from db.mongo import chat_collection, report_collection, meeting_collection
# from state.chat_state import set_state, get_state, clear_state

# import os
# import datetime

# router = APIRouter()


# class ChatRequest(BaseModel):
#     user_id: str
#     message: str


# # =========================
# # SAFE DATETIME PARSER
# # =========================
# def parse_datetime_safe(date, time):
#     try:
#         if "AM" in time or "PM" in time:
#             return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %I:%M %p")
#         else:
#             return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
#     except:
#         return datetime.datetime.utcnow()


# @router.post("/chat")
# def chat(req: ChatRequest):

#     user_id = req.user_id
#     message = req.message.strip()
#     msg_lower = message.lower()

#     # =========================
#     # SAVE USER MESSAGE
#     # =========================
#     chat_collection.update_one(
#         {"user_id": user_id},
#         {"$push": {"messages": {"role": "user", "message": message}}},
#         upsert=True
#     )

#     state = get_state(user_id)
#     final_response = None

#     # =========================
#     # 👋 GREETING
#     # =========================
#     if msg_lower in ["hi", "hello", "hey", "hii"]:
#         final_response = "👋 Hello! I can help you schedule meetings, reports, and Q&A."

#     # =========================
#     # 📜 HISTORY
#     # =========================
#     elif "history" in msg_lower:
#         chat_doc = chat_collection.find_one({"user_id": user_id})

#         if not chat_doc:
#             final_response = "📭 No history found"
#         else:
#             msgs = chat_doc.get("messages", [])[-10:]
#             text = "\n".join([f"{m['role']}: {m['message']}" for m in msgs])
#             final_response = f"🧾 Recent chat:\n\n{text}"

#     # =========================
#     # 📅 PREVIOUS MEETING (FIXED)
#     # =========================
#     elif "previous meeting" in msg_lower:

#         meeting = meeting_collection.find_one(
#             {"user_id": user_id},
#             sort=[("updated_at", -1), ("created_at", -1)]
#         )

#         if meeting:
#             final_response = f"""📅 Your last meeting:

# Date: {meeting.get('date')}
# Time: {meeting.get('time')}
# 👉 {meeting.get('meeting_url')}

# Do you want to update it? (yes/no)
# """

#             set_state(user_id, {
#                 "step": "ask_update_existing",
#                 "event_id": meeting.get("event_id")
#             })
#         else:
#             final_response = "📭 No previous meeting found"

#     # =========================
#     # 📄 REPORT FLOW
#     # =========================
#     elif "report" in msg_lower:

#         report = report_collection.find_one(
#             {"user_id": user_id},
#             sort=[("created_at", -1)]
#         )

#         if not report:
#             final_response = "📭 No report found"
#         else:
#             pdf_path = report.get("pdf_report_path")

#             if not pdf_path:
#                 final_response = "❌ Report not ready"
#             else:
#                 filename = os.path.basename(pdf_path)
#                 pdf_url = f"https://stimulatingly-glumpier-hannelore.ngrok-free.dev/reports/{filename}"

#                 set_state(user_id, {
#                     "step": "ask_pdf_qa",
#                     "pdf_path": pdf_path,
#                     "meeting_id": report.get("meeting_id")
#                 })

#                 final_response = f"""📄 Report ready
# 👉 {pdf_url}

# ❓ Ask questions from PDF? (yes/no)"""

#     # =========================
#     # PDF CONFIRM
#     # =========================
#     elif state and state.get("step") == "ask_pdf_qa":

#         if msg_lower in ["yes", "y"]:
#             create_vector_db(user_id, state["pdf_path"])

#             set_state(user_id, {
#                 "step": "pdf_qa",
#                 "pdf_path": state["pdf_path"],
#                 "meeting_id": state.get("meeting_id")
#             })

#             final_response = "🧠 Ask your question"

#         else:
#             clear_state(user_id)
#             final_response = "👍 Okay"

#     # =========================
#     # PDF QA MODE
#     # =========================
#     elif state and state.get("step") == "pdf_qa":

#         if msg_lower in ["exit", "stop"]:
#             clear_state(user_id)
#             final_response = "❌ Exited QA"
#         else:
#             final_response = ask_pdf(user_id, message)

#     # =========================
#     # SEND REPORT
#     # =========================
#     elif "send report" in msg_lower:

#         meeting_id = state.get("meeting_id") if state else None

#         if not meeting_id:
#             final_response = "❌ No meeting found"
#         else:
#             final_response = send_report_to_participants(user_id, meeting_id)

#     # =========================
#     # UPDATE EXISTING MEETING
#     # =========================
#     elif state and state.get("step") == "ask_update_existing":

#         if msg_lower in ["yes", "y"]:
#             set_state(user_id, {
#                 "step": "update_existing_meeting",
#                 "event_id": state["event_id"]
#             })
#             final_response = "🔄 Enter new date & time"
#         else:
#             clear_state(user_id)
#             final_response = "👍 Okay"

#     elif state and state.get("step") == "update_existing_meeting":

#         res = handle_meeting(user_id, message)

#         set_state(user_id, {
#             "step": "meeting_bot_confirm",
#             "meeting_data": res
#         })

#         final_response = f"""{res.get('message')}

# 🤖 Bot join meeting? (yes/no)"""

#     # =========================
#     # NEW MEETING
#     # =========================
#     elif msg_lower.startswith("schedule") or msg_lower.startswith("create meeting"):

#         res = handle_meeting(user_id, message)

#         if res.get("meeting_url"):
#             set_state(user_id, {
#                 "step": "meeting_confirm",
#                 "meeting_data": res
#             })

#             final_response = f"""📅 Meeting created
# 👉 {res['meeting_url']}

# ❓ Confirm meeting? (yes/no)"""
#         else:
#             final_response = res.get("message")

#     # =========================
#     # CONFIRM STEP 1
#     # =========================
#     elif state and state.get("step") == "meeting_confirm":

#         if msg_lower in ["yes", "y"]:
#             set_state(user_id, {
#                 "step": "meeting_bot_confirm",
#                 "meeting_data": state["meeting_data"]
#             })
#             final_response = "🤖 Bot join meeting? (yes/no)"
#         else:
#             set_state(user_id, {"step": "meeting_update"})
#             final_response = "🔄 Enter new date & time"

#     # =========================
#     # UPDATE LOOP
#     # =========================
#     elif state and state.get("step") == "meeting_update":

#         from services.parser import parse_meeting

#         parsed = parse_meeting(user_id, message)

#         if not parsed:
#             final_response = "❌ Invalid input"
#         else:
#             set_state(user_id, {
#                 "step": "meeting_reconfirm",
#                 "new_meeting": parsed
#             })

#             final_response = f"""📌 Updated:
# Date: {parsed.get('date')}
# Time: {parsed.get('time')}

# Confirm updated? (yes/no)"""

#     elif state and state.get("step") == "meeting_reconfirm":

#         if msg_lower in ["yes", "y"]:

#             updated_msg = f"meeting on {state['new_meeting']['date']} at {state['new_meeting']['time']}"
#             res = handle_meeting(user_id, updated_msg)

#             set_state(user_id, {
#                 "step": "meeting_bot_confirm",
#                 "meeting_data": res
#             })

#             final_response = f"""✅ Meeting confirmed
# 👉 {res.get('meeting_url')}

# 🤖 Bot join meeting? (yes/no)"""

#         else:
#             set_state(user_id, {"step": "meeting_update"})
#             final_response = "🔄 Enter new date & time again"

#     # =========================
#     # BOT JOIN
#     # =========================
#     elif state and state.get("step") == "meeting_bot_confirm":

#         meeting_data = state.get("meeting_data", {})

#         meeting_id = meeting_data.get("event_id")
#         meeting_url = meeting_data.get("meeting_url")

#         if msg_lower in ["yes", "y"]:

#             meeting = meeting_collection.find_one({"event_id": meeting_id})

#             start_dt = parse_datetime_safe(
#                 meeting.get("date"),
#                 meeting.get("time")
#             )

#             add_scheduled_meeting(
#                 job_id=meeting_id,
#                 meeting_url=meeting_url,
#                 scheduled_at_iso=start_dt.isoformat(),
#                 user_id=user_id
#             )

#             final_response = "🤖 Bot scheduled successfully ✅"

#         else:
#             final_response = "👍 Meeting created without bot"

#         clear_state(user_id)

#     # =========================
#     # DEFAULT
#     # =========================
#     if not final_response:
#         final_response = "❓ Try: schedule meeting at 7pm"

#     # =========================
#     # SAVE BOT MESSAGE
#     # =========================
#     chat_collection.update_one(
#         {"user_id": user_id},
#         {"$push": {"messages": {"role": "bot", "message": final_response}}}
#     )

#     return {"message": final_response}









from fastapi import APIRouter
from pydantic import BaseModel

from services.meeting_service import handle_meeting
from services.pdf_qa_service import ask_pdf, create_vector_db
from services.email_service import send_report_to_participants
from services.scheduler_service import add_scheduled_meeting

from db.mongo import chat_collection, report_collection, meeting_collection
from state.chat_state import set_state, get_state, clear_state

import os
import datetime

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str


def parse_datetime_safe(date, time):
    try:
        if "AM" in time or "PM" in time:
            return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %I:%M %p")
        return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except:
        return datetime.datetime.utcnow()


@router.post("/chat")
def chat(req: ChatRequest):

    user_id = req.user_id
    message = req.message.strip()
    msg_lower = message.lower()

    chat_collection.update_one(
        {"user_id": user_id},
        {"$push": {"messages": {"role": "user", "message": message}}},
        upsert=True
    )

    state = get_state(user_id)
    final_response = None

    # =========================
    # GREETING
    # =========================
    if msg_lower in ["hi", "hello", "hey", "hii"]:
        final_response = "👋 Hello! I can help with meetings, reports, and PDF Q&A."

    # =========================
    # HISTORY
    # =========================
    elif "history" in msg_lower:
        doc = chat_collection.find_one({"user_id": user_id})
        if not doc:
            final_response = "📭 No history"
        else:
            msgs = doc.get("messages", [])[-10:]
            final_response = "\n".join([f"{m['role']}: {m['message']}" for m in msgs])

    # =========================
    # REPORT FLOW
    # =========================
    elif "report" in msg_lower:

        report = report_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

        if not report:
            final_response = "📭 No report found"
        else:
            pdf_path = report.get("pdf_report_path")
            filename = os.path.basename(pdf_path)
            pdf_url = f"https://stimulatingly-glumpier-hannelore.ngrok-free.dev/reports/{filename}"

            set_state(user_id, {
                "step": "pdf_confirm",
                "pdf_path": pdf_path,
                "meeting_id": report.get("meeting_id")
            })

            final_response = f"""📄 Report ready
👉 {pdf_url}

❓ Do you want to ask questions from PDF? (yes/no)"""

    # =========================
    # PDF CONFIRM
    # =========================
    elif state and state.get("step") == "pdf_confirm":

        if msg_lower in ["yes", "y"]:
            create_vector_db(user_id, state["pdf_path"])
            set_state(user_id, {"step": "pdf_qa", "pdf_path": state["pdf_path"]})
            final_response = "🧠 Ask your question"

        else:
            clear_state(user_id)
            final_response = "👍 Okay"

    # =========================
    # PDF QA
    # =========================
    elif state and state.get("step") == "pdf_qa":

        if msg_lower in ["exit", "stop"]:
            clear_state(user_id)
            final_response = "❌ Exited PDF mode"
        else:
            final_response = ask_pdf(user_id, message)

    # =========================
    # PREVIOUS MEETING
    # =========================
    elif "previous meeting" in msg_lower:

        meeting = meeting_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

        if meeting:
            final_response = f"""📅 Last Meeting:
Date: {meeting.get('date')}
Time: {meeting.get('time')}
👉 {meeting.get('meeting_url')}

Do you want to update it? (yes/no)"""

            set_state(user_id, {
                "step": "ask_update_existing",
                "event_id": meeting.get("event_id")
            })

        else:
            final_response = "📭 No meeting found"

    # =========================
    # 🔥 STEP 1: ASK UPDATE CONFIRMATION (NEW FIX)
    # =========================
    elif state and state.get("step") == "ask_update_existing":

        if msg_lower in ["yes", "y"]:
            set_state(user_id, {
                "step": "final_update_confirm",
                "event_id": state["event_id"]
            })

            final_response = "⚠️ Final confirmation: Update meeting? (yes/no)"

        else:
            clear_state(user_id)
            final_response = "👍 Okay"

    # =========================
    # 🔥 FINAL CONFIRMATION BEFORE UPDATE
    # =========================
    elif state and state.get("step") == "final_update_confirm":

        if msg_lower in ["yes", "y"]:
            set_state(user_id, {
                "step": "meeting_update",
                "event_id": state["event_id"]
            })
            final_response = "🔄 Enter new date & time"

        else:
            clear_state(user_id)
            final_response = "👍 Update cancelled"

    # =========================
    # UPDATE LOOP (SAFE)
    # =========================
    elif state and state.get("step") == "meeting_update":

        from services.parser import parse_meeting

        parsed = parse_meeting(user_id, message)

        if not parsed:
            final_response = "❌ Invalid input, try again"
        else:
            set_state(user_id, {
                "step": "meeting_reconfirm",
                "new_meeting": parsed
            })

            final_response = f"""📌 Updated:
Date: {parsed.get('date')}
Time: {parsed.get('time')}

Confirm updated meeting? (yes/no)"""

    # =========================
    # RECONFIRM UPDATE LOOP
    # =========================
    elif state and state.get("step") == "meeting_reconfirm":

        if msg_lower in ["yes", "y"]:

            updated_msg = f"meeting on {state['new_meeting']['date']} at {state['new_meeting']['time']}"
            res = handle_meeting(user_id, updated_msg)

            set_state(user_id, {
                "step": "meeting_bot_confirm",
                "meeting_data": res
            })

            final_response = f"""✅ Meeting confirmed
👉 {res.get('meeting_url')}

🤖 Bot join meeting? (yes/no)"""

        else:
            set_state(user_id, {"step": "meeting_update"})
            final_response = "🔄 Enter again date & time"

    # =========================
    # NEW MEETING
    # =========================
    elif msg_lower.startswith("schedule"):

        res = handle_meeting(user_id, message)

        set_state(user_id, {
            "step": "meeting_confirm",
            "meeting_data": res
        })

        final_response = f"""📅 Meeting created
👉 {res.get('meeting_url')}

❓ Confirm meeting? (yes/no)"""

    # =========================
    # CONFIRM MEETING
    # =========================
    elif state and state.get("step") == "meeting_confirm":

        if msg_lower in ["yes", "y"]:
            set_state(user_id, {
                "step": "meeting_bot_confirm",
                "meeting_data": state["meeting_data"]
            })
            final_response = "🤖 Bot join meeting? (yes/no)"

        else:
            set_state(user_id, {"step": "meeting_update"})
            final_response = "🔄 Enter new date & time"

    # =========================
    # BOT JOIN
    # =========================
    elif state and state.get("step") == "meeting_bot_confirm":

        data = state.get("meeting_data", {})

        if msg_lower in ["yes", "y"]:

            meeting = meeting_collection.find_one({"event_id": data.get("event_id")})

            start_dt = parse_datetime_safe(meeting.get("date"), meeting.get("time"))

            add_scheduled_meeting(
                job_id=data.get("event_id"),
                meeting_url=data.get("meeting_url"),
                scheduled_at_iso=start_dt.isoformat(),
                user_id=user_id
            )

            final_response = "🤖 Bot scheduled successfully ✅"

        else:
            final_response = "👍 Meeting created without bot"

        clear_state(user_id)

    # =========================
    # DEFAULT
    # =========================
    if not final_response:
        final_response = "❓ Try: schedule meeting"

    chat_collection.update_one(
        {"user_id": user_id},
        {"$push": {"messages": {"role": "bot", "message": final_response}}}
    )

    return {"message": final_response}