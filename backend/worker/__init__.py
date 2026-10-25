from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseWorker
    from .probability_worker import ProbabilityWorker
    from .event_consumer import EventConsumer, event_consumer
    from .chat_summarizer import ChatSummarizerWorker
    from .mongodb import MongoDbWorker


def __getattr__(name: str):
    if name == "BaseWorker":
        from .base import BaseWorker
        return BaseWorker
    elif name == "ProbabilityWorker":
        from .probability_worker import ProbabilityWorker
        return ProbabilityWorker
    elif name == "EventConsumer":
        from .event_consumer import EventConsumer
        return EventConsumer
    elif name == "event_consumer":
        from .event_consumer import event_consumer
        return event_consumer
    elif name == "ChatSummarizerWorker":
        from .chat_summarizer import ChatSummarizerWorker
        return ChatSummarizerWorker
    elif name == "MongoDbWorker":
        from .mongodb import MongoDbWorker
        return MongoDbWorker
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "BaseWorker",
    "ProbabilityWorker",
    "EventConsumer",
    "event_consumer",
    "ChatSummarizerWorker",
    "MongoDbWorker",
]
