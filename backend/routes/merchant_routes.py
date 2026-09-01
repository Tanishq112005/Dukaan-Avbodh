from fastapi import APIRouter, Depends, HTTPException
from middleware.role_middleware import require_role
from models.user import UserRole
from services.audit_logger import audit_logger
from repositories.chat_audit_repository import chat_audit_repo

router = APIRouter(prefix="/merchant", tags=["Merchant"])

@router.get("/audit-logs")
async def get_audit_logs(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all money/action audit logs from MongoDB."""
    cursor = audit_logger.collection.find().sort("timestamp", -1).limit(200)
    logs = await cursor.to_list(length=200)
    
    # Convert ObjectId to string for JSON serialization
    for log in logs:
        log["_id"] = str(log["_id"])
        
    return {"logs": logs}

@router.get("/chat-threads")
async def get_all_chat_threads(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all chat threads across all users for auditing."""
    cursor = chat_audit_repo.collection.find().sort("updated_at", -1).limit(100)
    threads = await cursor.to_list(length=100)
    
    for thread in threads:
        thread["_id"] = str(thread["_id"])
        
    return {"threads": threads}
