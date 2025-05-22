from itsdangerous import URLSafeTimedSerializer
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")

s = URLSafeTimedSerializer(SECRET_KEY)

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

def generate_verification_token(email):
    return s.dumps(email, salt=SECURITY_PASSWORD_SALT)

def verify_email_token(token, expiration=3600):
    try:
        email = s.loads(token, salt=SECURITY_PASSWORD_SALT, max_age=expiration)
        return email
    except Exception:
        return False

async def send_verification_email(email: str, token: str):
    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Click to verify your email: http://localhost:8000/auth/verify-email?token={token}",
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_reset_password_email(email: str, token: str):
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=f"Click to reset your password: http://localhost:8000/auth/reset-password?token={token}",
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)


if __name__ == "__main__":
    import asyncio

    email_input = input("📧 Enter email to generate reset token: ").strip()

    token = generate_verification_token(email_input)
    reset_link = f"http://localhost:8000/auth/reset-password/{token}"

    print("\n🔐 Generated token:")
    print(token)
    print("\n🔗 Reset link:")
    print(reset_link)

    # Ask to send email directly
    send_now = input("\nDo you want to send this reset link via email? (yes/no): ").strip().lower()
    if send_now == "yes":
        asyncio.run(send_reset_password_email(email_input, token))
        print("✅ Email sent.")
    else:
        print("📭 Email not sent.")
