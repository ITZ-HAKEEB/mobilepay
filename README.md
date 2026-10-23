# MOBILEPAY starter

Python/FastAPI + MongoDB API, simple admin page, and landing page. This starter is not yet connected to the `ITZ-HAKEEB/MOBILEPAY` source tree.

## Included
- OTP login API; Twilio Verify can send/verify SMS OTPs.
- Demo OTP is local-development-only and must be disabled in production.
- JWT bearer tokens.
- MongoDB user records and demo payment intents/history.
- Basic process-local rate limiting (replace with Redis for multi-instance production).
- Admin stats protected by `X-Admin-Key`.
- Landing page with configurable name, creator, Instagram link, APK URL, and optional promo text.
- Docker, Heroku `Procfile`, `heroku.yml`, `app.json`.

## Important payment limitation
`POST /api/payment-intents` only writes a demo record. It does NOT make a UPI payment, verify a QR payment, or move money. For live UPI, integrate an authorized bank/payment partner after onboarding, security review, and sandbox testing. Eligibility and guardian-consent requirements can vary for minors; follow the partner's requirements and applicable law.

## 1. Local setup
Install Python 3.12 and MongoDB, then:

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`. For local demo only use:
`ENVIRONMENT=development`, `OTP_PROVIDER=demo`, `ENABLE_DEMO_OTP=true`.
Run:
```bash
uvicorn main:app --reload
```
Open `http://127.0.0.1:8000`, `/docs`, or `/admin`. Demo code is `123456` only when demo mode is enabled outside production.

## 2. Twilio SMS OTP
Create a Twilio Verify service and configure `OTP_PROVIDER=twilio`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_VERIFY_SERVICE_SID`. Confirm sender/service availability for your target country. Never commit credentials. Use test credentials/sandbox where available before launch.

## 3. Heroku
- Create the app and set Config Vars from `.env.example` (do not set demo OTP in production).
- Set `MONGODB_URI`, `SECRET_KEY`, `ADMIN_API_KEY`, and Twilio values.
- Deploy the repository. For container stack use `heroku.yml`; for buildpack use `Procfile` and `requirements.txt`. Do not configure both deployment methods inconsistently.
- Use a managed MongoDB provider with authentication, TLS, backups, and network access controls.

## 4. VPS with Docker
```bash
cp .env.example .env
# Edit .env with production secrets; never upload it to GitHub.
docker build -t mobilepay .
docker run -d --name mobilepay --restart unless-stopped --env-file .env -p 8000:8000 mobilepay
```
Put a reverse proxy with HTTPS (Caddy/Nginx) in front; restrict admin access. Back up MongoDB.

## 5. Security before public launch
- Use a long random `SECRET_KEY` and separate random `ADMIN_API_KEY`.
- Set `ENVIRONMENT=production`, `OTP_PROVIDER=twilio`, `ENABLE_DEMO_OTP=false`.
- Restrict `CORS_ORIGINS` to your real frontend domain.
- Replace process-local rate limiting with Redis-backed rate limits, plus per-phone OTP throttling and monitoring.
- Add privacy policy, terms, data deletion, audit, abuse handling, secure backups, and independent security review.
- Do not store UPI PINs, card PINs, OTPs, or bank passwords.
- Real payments require an authorized partner and approval; this starter is demo-only.

## API quick list
- `GET /health`
- `POST /api/auth/request-otp` body `{"phone":"+919876543210"}`
- `POST /api/auth/verify-otp` body `{"phone":"+919876543210","code":"123456"}`
- `GET /api/me` with `Authorization: Bearer <token>`
- `POST /api/payment-intents` with bearer token, body `{"amount_paise":1000,"currency":"INR","note":"demo"}`
- `GET /api/payment-history` with bearer token
- `GET /api/admin/stats` with `X-Admin-Key: <ADMIN_API_KEY>`

## Android app
`mobile_app/` is a placeholder Flutter client. Connect it to the deployed API only after the backend configuration and security review are complete.
