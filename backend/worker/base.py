from abc import ABC, abstractmethod

class BaseWorker(ABC):
    """
    Base interface for all queue workers.
    """
    
    @classmethod
    @abstractmethod
    def run(cls, data: dict):
        """
        The entry point method that RQ will execute.
        Expects a dictionary payload containing job information.
        """
        pass
