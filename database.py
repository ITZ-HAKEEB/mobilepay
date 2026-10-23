from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

_client: AsyncIOMotorClient | None = None

async def connect_db():
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    await _client.admin.command("ping")
    db = _client[settings.mongodb_db]
    await db.users.create_index("phone", unique=True)
    await db.otp_attempts.create_index("created_at", expireAfterSeconds=3600)
    await db.audit_logs.create_index("created_at", expireAfterSeconds=60 * 60 * 24 * 90)
    return db

async def close_db():
    global _client
    if _client is not None:
        _client.close()
        _client = None
