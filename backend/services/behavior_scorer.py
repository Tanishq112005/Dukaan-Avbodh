from datetime import datetime
from repositories.user_event_repository import UserEventRepository
from models.user_event import EventType

class BehaviorScorer:
    EVENT_WEIGHTS = {
        "purchased": 5.0,
        "added_to_cart": 3.0,
        "suggestion_accepted": 3.0,
        "viewed": 1.0,
        "suggestion_skipped": -2.0,
    }
    CURRENT_SESSION_BOOST = 1.5   # abhi ke session ke actions 1.5x zyada weight

    def __init__(self):
        self.event_repo = UserEventRepository()

    async def get_category_affinity(self, user_id: int) -> dict[str, float]:
        events = await self.event_repo.get_events_for_user(user_id)

        session_starts = [e.timestamp for e in events if e.event_type == EventType.SESSION_START]
        current_session_start = max(session_starts) if session_starts else None

        scores: dict[str, float] = {}
        now = datetime.utcnow()

        for event in events:
            if event.event_type == EventType.SESSION_START:
                continue   # yeh khud koi "interest" signal nahi hai, sirf marker hai

            weight = self.EVENT_WEIGHTS.get(event.event_type.value, 0.0)
            days_old = (now - event.timestamp).days
            recency_factor = max(0.5, 1.0 - (days_old / 60))

            if current_session_start and event.timestamp >= current_session_start:
                recency_factor *= self.CURRENT_SESSION_BOOST

            scores[event.category] = scores.get(event.category, 0.0) + (weight * recency_factor)

        return scores


behavior_scorer = BehaviorScorer()