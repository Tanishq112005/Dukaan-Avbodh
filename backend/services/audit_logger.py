# services/audit_logger.py
from abc import ABC, abstractmethod


class AuditLogger(ABC):
    @abstractmethod
    async def log_action(self, action: str, reason: str, result: str) -> None:
        pass


class ConsoleAuditLogger(AuditLogger):
    """Temporary implementation — jab tak MongoDB nahi lagta, sirf console/terminal mein print karega."""

    async def log_action(self, action: str, reason: str, result: str) -> None:
        print(f"[AUDIT] action={action} | reason={reason} | result={result}")


# poore project mein isi shared instance ko use karo
audit_logger = ConsoleAuditLogger()


