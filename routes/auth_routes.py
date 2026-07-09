from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from auth.google_auth import get_auth_url, handle_callback

router = APIRouter()


# =========================
# LOGIN
# =========================
@router.get("/auth/login")
def login():
    auth_url = get_auth_url()
    return RedirectResponse(auth_url)



from fastapi.responses import RedirectResponse

STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")

@router.get("/auth/callback")
def callback(request: Request):

    full_url = str(request.url)
    state = request.query_params.get("state")

    result = handle_callback(full_url, state)

    if "error" in result:
        # login fail hua toh error ke saath wapas bhejo
        return RedirectResponse(f"{STREAMLIT_URL}/?error=login_failed")

    user_id = result.get("user_id")
    email = result.get("email")

    # ✅ Automatic redirect with user_id in URL
    return RedirectResponse(f"{STREAMLIT_URL}/?user_id={user_id}&email={email}")
