from abc import ABC, abstractmethod
from datetime import datetime
from config.mogodbconfig import NoSqlClient

class AuditLogger(ABC):
    @abstractmethod
    async def log_action(self, action: str, reason: str, result: str, user_id: int = None) -> None:
        pass


class MongoAuditLogger(AuditLogger):
    """MongoDB implementation for audit trailing - Merchant can view this data."""
    def __init__(self):
        self.no_sql_client = NoSqlClient()
        self.db = self.no_sql_client.get_database("dukaan_audit")
        self.collection = self.db["audit_logs"]

    async def log_action(self, action: str, reason: str, result: str, user_id: int = None) -> None:
        # Also print to console for local debugging
        print(f"[AUDIT] action={action} | reason={reason} | result={result} | user_id={user_id}")
        
        await self.collection.insert_one({
            "action": action,
            "reason": reason,
            "result": result,
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        })


# Poore project mein isi shared instance ko use karo
audit_logger = MongoAuditLogger()


