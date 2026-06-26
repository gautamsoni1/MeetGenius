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



@router.get("/auth/callback")
def callback(request: Request):

    full_url = str(request.url)
    state = request.query_params.get("state")

    result = handle_callback(full_url, state)

    return result   # ❌ NO redirect anymore