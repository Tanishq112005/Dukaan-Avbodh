import os
from abc import ABC, abstractmethod
from datetime import datetime

class AuditLogger(ABC):
    @abstractmethod
    async def log_action(self, action: str, reason: str, result: str, user_id: int = None, thread_id: str = None, metadata: dict = None) -> None:
        pass


class DummyAuditLogger(AuditLogger):
    async def log_action(self, action: str, reason: str, result: str, user_id: int = None, thread_id: str = None, metadata: dict = None) -> None:
        print(f"[AUDIT DUMMY] action={action} | reason={reason} | result={result} | user_id={user_id} | thread_id={thread_id}")

try:
    from config.mogodbconfig import nosql_client
    
    class MongoAuditLogger(AuditLogger):
        """MongoDB implementation for audit trailing - Merchant can view this data."""
        def __init__(self):
            self.db = nosql_client.get_database("dukaan_audit")
            self.collection = self.db["audit_logs"]

        async def log_action(self, action: str, reason: str, result: str, user_id: int = None, thread_id: str = None, metadata: dict = None) -> None:
            # Also print to console for local debugging
            print(f"[AUDIT] action={action} | reason={reason} | result={result} | user_id={user_id} | thread_id={thread_id}")
            
            doc = {
                "action": action,
                "reason": reason,
                "result": result,
                "user_id": user_id,
                "thread_id": thread_id,
                "timestamp": datetime.utcnow()
            }
            if metadata:
                doc["metadata"] = metadata
            try:
                await self.collection.insert_one(doc)
            except Exception as e:
                print(f"[AUDIT WARNING] Could not write to MongoDB (is it running?): {e}")

    # Poore project mein isi shared instance ko use karo
    audit_logger = MongoAuditLogger()
except ImportError:
    print("[WARNING] 'pymongo' (MongoDB client) is not installed. Using DummyAuditLogger.")
    audit_logger = DummyAuditLogger()


