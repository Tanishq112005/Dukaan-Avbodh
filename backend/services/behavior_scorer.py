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
    
    # Advanced Multipliers as discussed
    CURRENT_SESSION_BOOST = 3.0
    PAST_SESSION_BOOST = 1.5
    GLOBAL_TREND_BOOST = 0.5

    def __init__(self):
        self.event_repo = UserEventRepository()

    async def get_category_affinity(self, user_id: int) -> dict[str, float]:
        # 1. User ke saare personal events
        user_events = await self.event_repo.get_events_for_user(user_id)
        
        # 2. Dusre users (Global/Crowd) ke recent events
        global_events = await self.event_repo.get_recent_global_events(limit=200)

        session_starts = [e.timestamp for e in user_events if e.event_type == EventType.SESSION_START]
        current_session_start = max(session_starts) if session_starts else None

        scores: dict[str, float] = {}
        now = datetime.utcnow()

        # Phase 1: Score User's own events (Current + Past)
        for event in user_events:
            if event.event_type == EventType.SESSION_START or not event.category:
                continue

            weight = self.EVENT_WEIGHTS.get(event.event_type.value, 0.0)
            
            # Recency factor: naye events ko zyada importance
            days_old = (now - event.timestamp).days
            recency_factor = max(0.2, 1.0 - (days_old / 60))

            # Agar yeh event current session ka hai, toh highest boost
            if current_session_start and event.timestamp >= current_session_start:
                final_weight = weight * recency_factor * self.CURRENT_SESSION_BOOST
            else:
                # Agar previous sessions ka hai
                final_weight = weight * recency_factor * self.PAST_SESSION_BOOST

            scores[event.category] = scores.get(event.category, 0.0) + final_weight

        # Phase 2: Score Other Users (Global Trends) to handle Cold Starts
        for event in global_events:
            # Apne khud ke events ya invalid events exclude karo
            if event.user_id == user_id or event.event_type == EventType.SESSION_START or not event.category:
                continue 
                
            weight = self.EVENT_WEIGHTS.get(event.event_type.value, 0.0)
            
            # Crowd events get the lowest multiplier
            final_weight = weight * self.GLOBAL_TREND_BOOST
            scores[event.category] = scores.get(event.category, 0.0) + final_weight

        return scores

    def estimate_purchase_probability(self, category_score: float) -> float:
        """Category affinity score ko ek estimated purchase probability % mein convert karta hai."""
        return round(min(95.0, max(5.0, category_score * 10)), 2)

    async def get_current_gender_context(self, user_id: int, limit: int = 10) -> str | None:
        """
        User abhi kis gender section mein browse kar raha hai, yeh detect karta hai
        recent VIEWED events se. Cart khali hone par bhi (jo normal hai jab tak user
        kuch add na kare) yeh sahi gender signal deta hai — taaki men's section
        browse karte waqt women's suggestions na aayein.

        CURRENT session ke views ko priority deta hai (sabse accurate — abhi kya
        dekh raha hai), tabhi purani sessions pe fallback karta hai.
        """
        from repositories.product_repository import ProductRepository
        product_repo = ProductRepository()

        events = await self.event_repo.get_events_for_user(user_id)

        session_starts = [e.timestamp for e in events if e.event_type == EventType.SESSION_START]
        current_session_start = max(session_starts) if session_starts else None

        viewed = [e for e in events if e.event_type == EventType.VIEWED and e.product_id]

        if current_session_start:
            current_views = [e for e in viewed if e.timestamp >= current_session_start]
            if current_views:
                viewed = current_views

        viewed_sorted = sorted(viewed, key=lambda e: e.timestamp, reverse=True)[:limit]

        genders = []
        for e in viewed_sorted:
            p = await product_repo.get_by_id(e.product_id)
            if p and p.gender and p.gender != "unisex":
                genders.append(p.gender)

        if not genders:
            return None
        return max(set(genders), key=genders.count)

behavior_scorer = BehaviorScorer()