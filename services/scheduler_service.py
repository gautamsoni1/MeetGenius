import json
import os
from datetime import datetime
import requests
from datetime import datetime, timezone
from config.config import BACKEND_URL

RECORD_API = f"{BACKEND_URL}/record"
JOBS_FILE = "scheduled_jobs.json"


def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def add_scheduled_meeting(job_id, meeting_url, scheduled_at_iso, user_id):

    if not job_id or not meeting_url or meeting_url == "None":
        print("❌ Invalid job data — skipped")
        return

    jobs = load_jobs()

    jobs[job_id] = {
        "meeting_url": meeting_url,
        "scheduled_at": scheduled_at_iso,
        "user_id": user_id,
        "status": "pending"
    }

    save_jobs(jobs)

    print(f"✅ Job Scheduled: {job_id}")

def check_jobs():
    jobs = load_jobs()
    now = datetime.now(timezone.utc)          # ✅ UTC-aware, Render server ka clock
    for job_id, job in jobs.items():
        if job.get("status") != "pending":
            continue
        meeting_url = job.get("meeting_url")
        if not meeting_url:
            job["status"] = "failed"
            continue

        scheduled = datetime.fromisoformat(job["scheduled_at"])
        if scheduled.tzinfo is None:
            # agar scheduled_at_iso naive hai (IST bina offset ke likha gaya), UTC treat mat karo
            scheduled = scheduled.replace(tzinfo=timezone.utc)

        print(f"[check_jobs] job={job_id} now(UTC)={now} scheduled={scheduled}")  # 👈 debug line

        if now >= scheduled:
            print(f"🚀 Running Job: {job_id}")
            try:
                res = requests.post(RECORD_API, json={
                    "meeting_url": meeting_url,
                    "meeting_id": job_id,
                    "user_id": job["user_id"]
                }, timeout=30)
                print(f"[check_jobs] RECORD_API status={res.status_code} body={res.text}")
                job["status"] = "done" if res.status_code == 200 else "failed"
            except Exception as e:
                print(f"❌ [check_jobs] request failed: {e}")
                job["status"] = "failed"
    save_jobs(jobs)


def start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_jobs, "interval", seconds=30)
    scheduler.start()

    print("⏰ Scheduler running")
