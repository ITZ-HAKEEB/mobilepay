from contextlib import asynccontextmanager
from datetime import datetime, timezone
import re
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from bson import ObjectId
from database import connect_db, close_db
from config import settings
from auth import send_otp, verify_otp, create_access_token, current_user
from rate_limit import rate_limit

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await connect_db()
    yield
    await close_db()

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class OTPRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=16, description="E.164 format, e.g. +919876543210")

class OTPVerify(BaseModel):
    phone: str = Field(min_length=8, max_length=16)
    code: str = Field(min_length=4, max_length=10)

class PaymentIntent(BaseModel):
    amount_paise: int = Field(gt=0, le=10000000)
    currency: str = Field(default="INR", pattern="^INR$")
    note: str = Field(default="", max_length=120)

def get_db(request: Request):
    return request.app.state.db

def validate_phone(phone: str):
    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        raise HTTPException(status_code=422, detail="Use international phone format, e.g. +919876543210")

def require_admin(x_admin_key: str | None = Header(default=None), db=Depends(get_db)):
    if not x_admin_key or not secrets_equal(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=403, detail="Admin access denied")
    return True

def secrets_equal(a: str, b: str) -> bool:
    import hmac
    return hmac.compare_digest(a, b)

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, "app_name": settings.app_name, "made_by": settings.made_by,
        "instagram_url": settings.instagram_url, "apk_url": settings.apk_download_url,
        "promo_user_text": settings.promo_user_text,
    })

@app.post("/api/auth/request-otp", dependencies=[Depends(rate_limit(5, 300))])
async def request_otp(payload: OTPRequest, db=Depends(get_db)):
    validate_phone(payload.phone)
    result = send_otp(payload.phone)
    await db.otp_attempts.insert_one({
        "phone": payload.phone, "created_at": datetime.now(timezone.utc), "purpose": "login"
    })
    response = {"message": "If the number is eligible, a verification code has been sent."}
    if result.get("demo_code"):
        response["demo_code"] = result["demo_code"]  # Local development only; disabled in production.
    return response

@app.post("/api/auth/verify-otp", dependencies=[Depends(rate_limit(8, 300))])
async def verify_login(payload: OTPVerify, db=Depends(get_db)):
    validate_phone(payload.phone)
    if not verify_otp(payload.phone, payload.code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    now = datetime.now(timezone.utc)
    await db.users.update_one(
        {"phone": payload.phone},
        {"$set": {"phone": payload.phone, "last_login": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return {"access_token": create_access_token(payload.phone), "token_type": "bearer", "expires_in": 43200}

@app.get("/api/me")
async def me(phone: str = Depends(current_user), db=Depends(get_db)):
    user = await db.users.find_one({"phone": phone}, {"_id": 0, "phone": 1, "created_at": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("created_at"):
        user["created_at"] = user["created_at"].isoformat()
    return user

@app.post("/api/payment-intents", dependencies=[Depends(rate_limit(10, 60))])
async def create_payment_intent(payload: PaymentIntent, phone: str = Depends(current_user), db=Depends(get_db)):
    # DEMO ONLY: this records an intent; it does not initiate or settle a real UPI payment.
    doc = {
        "user_phone": phone, "amount_paise": payload.amount_paise, "currency": payload.currency,
        "note": payload.note, "status": "demo_pending",
        "created_at": datetime.now(timezone.utc), "real_payment": False
    }
    result = await db.payment_intents.insert_one(doc)
    return {"id": str(result.inserted_id), "status": "demo_pending",
            "message": "Demo record only. No money was transferred."}

@app.get("/api/payment-history")
async def payment_history(phone: str = Depends(current_user), db=Depends(get_db)):
    cursor = db.payment_intents.find({"user_phone": phone}, {"user_phone": 0}).sort("created_at", -1).limit(50)
    rows = []
    async for row in cursor:
        rows.append({
            "id": str(row["_id"]), "amount_paise": row["amount_paise"],
            "currency": row["currency"], "note": row["note"], "status": row["status"],
            "created_at": row["created_at"].isoformat(), "real_payment": False
        })
    return {"items": rows}

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request, "app_name": settings.app_name})

@app.get("/api/admin/stats", dependencies=[Depends(require_admin)])
async def admin_stats(db=Depends(get_db)):
    return {
        "users": await db.users.count_documents({}),
        "demo_payment_intents": await db.payment_intents.count_documents({}),
        "notice": "Counts are database records; payment intents are not completed payments."
    }

@app.get("/api/admin/recent-users", dependencies=[Depends(require_admin)])
async def admin_recent_users(db=Depends(get_db)):
    rows = []
    cursor = db.users.find({}, {"phone": 1, "created_at": 1, "_id": 0}).sort("created_at", -1).limit(100)
    async for user in cursor:
        rows.append({"phone": user.get("phone", ""), "created_at": user.get("created_at").isoformat() if user.get("created_at") else None})
    return {"items": rows}
