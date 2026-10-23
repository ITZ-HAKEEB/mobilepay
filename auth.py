from datetime import datetime, timedelta, timezone
import secrets
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from twilio.rest import Client
from config import settings

ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int((now + timedelta(hours=12)).timestamp())}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def read_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Missing subject")
        return subject
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token required")
    return read_token(credentials.credentials)

def send_otp(phone: str):
    if settings.otp_provider.lower() == "twilio":
        if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_verify_service_sid]):
            raise HTTPException(status_code=503, detail="SMS verification provider is not configured")
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        try:
            client.verify.v2.services(settings.twilio_verify_service_sid).verifications.create(
                to=phone, channel="sms"
            )
        except Exception:
            # Do not leak provider internals or whether an account exists.
            raise HTTPException(status_code=502, detail="Could not send verification code")
        return {"demo_code": None}
    if settings.otp_provider == "demo" and settings.enable_demo_otp and settings.environment != "production":
        return {"demo_code": "123456"}
    raise HTTPException(status_code=503, detail="OTP provider unavailable")

def verify_otp(phone: str, code: str) -> bool:
    if settings.otp_provider.lower() == "twilio":
        if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_verify_service_sid]):
            return False
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        try:
            result = client.verify.v2.services(settings.twilio_verify_service_sid).verification_checks.create(
                to=phone, code=code
            )
            return result.status == "approved"
        except Exception:
            return False
    return (
        settings.otp_provider == "demo"
        and settings.enable_demo_otp
        and settings.environment != "production"
        and secrets.compare_digest(code, "123456")
    )
