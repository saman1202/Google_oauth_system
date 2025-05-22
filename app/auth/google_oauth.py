import os
import httpx
import json
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

def get_google_auth_url():
    print("🔑 GOOGLE_CLIENT_ID:", GOOGLE_CLIENT_ID)
    print("🔑 GOOGLE_CLIENT_SECRET:", GOOGLE_CLIENT_SECRET)
    print("🔁 REDIRECT_URI:", REDIRECT_URI)

    scope = "openid email profile"
    return (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
    )


def get_user_info_from_google(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    with httpx.Client() as client:
        print("📤 Sending token request...")
        response = client.post(token_url, data=token_data, headers=headers)
        print("📡 Status:", response.status_code)
        print("📦 Body:", json.dumps(response.json(), indent=2))

        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")

        token_json = response.json()
        if "id_token" not in token_json:
            raise Exception("Missing 'id_token' in token response")

        id_info = id_token.verify_oauth2_token(
            token_json["id_token"],
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        return {
            "name": id_info.get("name"),
            "email": id_info.get("email"),
            "sub": id_info.get("sub")
        }
