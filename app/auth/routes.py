from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth.google_oauth import get_google_auth_url, get_user_info_from_google
from app.auth.email_utils import send_verification_email, verify_email_token, send_reset_password_email
from app.auth.password_utils import hash_password, verify_password
from jose import jwt
import os
from app.auth.email_utils import generate_verification_token
import json
router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(password)
    new_user = models.User(name=name, email=email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = generate_verification_token(email)
    send_verification_email(email, token)
    return templates.TemplateResponse("verify.html", {"request": request, "email": email})

@router.get("/verify")
def verify_email(request: Request, token: str, db: Session = Depends(get_db)):
    email = verify_email_token(token)
    if not email:
        return templates.TemplateResponse("verify.html", {"request": request, "error": "Invalid or expired token."})

    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        user.is_verified = True
        db.commit()
    return RedirectResponse("/auth/login", status_code=status.HTTP_302_FOUND)

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "User not found"})

    if not user.hashed_password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "This account uses Google login. Please use Google or set a password."
        })

    if not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Incorrect password"})

    if not user.is_verified:
        return templates.TemplateResponse("verify.html", {"request": request, "email": email})

    request.session["user"] = {"id": user.id, "email": user.email}
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_form(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request, "step": "request"})
@router.post("/forgot-password")
async def forgot_password(email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        token = generate_verification_token(email)
        await send_reset_password_email(email, token)  # ✅ use await here
    return RedirectResponse("/auth/login", status_code=status.HTTP_302_FOUND)

@router.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_form(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "step": "reset", "token": token})

@router.post("/reset-password")
def reset_password(token: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    print("Token received from form:", token)
    email = verify_email_token(token)

    if not email:
        print("Invalid or expired token")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_password)
    db.commit()
    print("✅ Password updated for:", user.email)
    return RedirectResponse("/auth/login", status_code=status.HTTP_302_FOUND)

@router.get("/change-password", response_class=HTMLResponse)
def change_password_form(request: Request):
    return templates.TemplateResponse("change_password.html", {"request": request})

@router.post("/change-password")
def change_password(request: Request, old_password: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    user_data = request.session.get("user")
    if not user_data:
        return RedirectResponse("/auth/login", status_code=status.HTTP_302_FOUND)

    user = db.query(models.User).filter(models.User.id == user_data["id"]).first()
    if not verify_password(old_password, user.hashed_password):
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Incorrect current password"})

    user.hashed_password = hash_password(new_password)
    db.commit()
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@router.get("/google/login")
def google_login():
    url = get_google_auth_url()
    return RedirectResponse(url)


@router.get("/google/callback")
def google_callback(request: Request, code: str = None, db: Session = Depends(get_db)):
    import traceback
    try:
        print("📥 CALLBACK REACHED")
        print("🔐 Code received:", code)

        if not code:
            raise Exception("Missing 'code' in callback URL")

        user_info = get_user_info_from_google(code)
        print("✅ User Info from Google:", json.dumps(user_info, indent=2))

        # Save user if doesn't exist
        user = db.query(models.User).filter(models.User.email == user_info["email"]).first()
        if not user:
            user = models.User(
                name=user_info["name"],
                email=user_info["email"],
                google_id=user_info["sub"],
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Store in session
        request.session["user"] = {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }

        print("🎯 Session saved:", request.session["user"])
        return RedirectResponse("/dashboard")

    except Exception as e:
        print("❌ Google login failed!")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Google login failed")

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=302)
