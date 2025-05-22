from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import uvicorn
import logging
logging.basicConfig(level=logging.DEBUG)

# ✅ Import routes from the correct location
from app.auth.routes import router as auth_router


app = FastAPI()

# ✅ Add session middleware (for login sessions)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),  # Make sure .env has this
    max_age=60 * 60 * 24  # Session valid for 1 day
)

# ✅ Template directory setup
templates = Jinja2Templates(directory="app/templates")

# ✅ Include authentication and dashboard routers
app.include_router(auth_router, prefix="/auth")


# ✅ Redirect root to login
@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/auth/login")
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_name": user.get("name", "Guest"),
        "user_email": user.get("email", "N/A")
    })

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)
