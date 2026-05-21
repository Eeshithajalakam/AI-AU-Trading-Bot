from typing import Dict, Any, List
import random
from datetime import datetime, timedelta

class NewsIntelligence:
    def __init__(self):
        # Simulated upcoming calendar events (In production, wire to Forexfactory/NewsAPI)
        self.economic_events = [
            {"id": "evt_1", "event": "US CPI (YoY)", "impact": "HIGH", "asset_focus": "USD", "time_offset_min": 15},
            {"id": "evt_2", "event": "FOMC Rate Decision", "impact": "EXTREME", "asset_focus": "USD", "time_offset_min": 120},
            {"id": "evt_3", "event": "Initial Jobless Claims", "impact": "MEDIUM", "asset_focus": "USD", "time_offset_min": -30},
            {"id": "evt_4", "event": "Geopolitical Tensions Update", "impact": "HIGH", "asset_focus": "XAU", "time_offset_min": 8}
        ]
        self.base_sentiment = 55.0  # 0 (Extreme Bearish XAU) to 100 (Extreme Bullish XAU)
        self.last_update = datetime.utcnow()

    def analyze_current_environment(self) -> Dict[str, Any]:
        """
        Analyzes the macroeconomic environment and returns a risk block.
        If a HIGH or EXTREME impact event is happening within +/- 15 minutes, trading should pause.
        """
        now = datetime.utcnow()
        time_elapsed_minutes = (now - self.last_update).total_seconds() / 60.0
        
        # Only simulate shifts if actual time passed, to prevent rapid bouncing
        if time_elapsed_minutes >= 1.0:
            self.last_update = now
            for evt in self.economic_events:
                evt["time_offset_min"] -= 1  # Countdown
                if evt["time_offset_min"] < -60:
                    evt["time_offset_min"] = random.randint(60, 1440) # Reschedule

            # Simulate dynamic sentiment (geopolitics boosts gold, strong USD hurts gold)
            self.base_sentiment += (random.random() - 0.5) * 4.0
            self.base_sentiment = max(20.0, min(self.base_sentiment, 80.0))

        # Find active or impending high impact events
        danger_zone = False
        active_events = []
        for evt in self.economic_events:
            if evt["impact"] in ["HIGH", "EXTREME"]:
                # Pause trading 15 mins before and 15 mins after a major event
                if -15 <= evt["time_offset_min"] <= 15:
                    danger_zone = True
                    active_events.append(evt["event"])

        # Risk score calculation (0 = safe, 100 = extreme danger/halt trading)
        news_risk_score = 20
        if danger_zone:
            news_risk_score = 95
        elif self.base_sentiment > 70 or self.base_sentiment < 30:
            news_risk_score = 50 # Heightened volatility
        
        # Determine overall bias
        if self.base_sentiment > 60:
            bias = "BULLISH_XAU"
        elif self.base_sentiment < 40:
            bias = "BEARISH_XAU"
        else:
            bias = "NEUTRAL"

        return {
            "timestamp": now.isoformat(),
            "danger_zone": danger_zone,
            "news_risk_score": news_risk_score,
            "active_high_impact_events": active_events,
            "macro_sentiment_score": round(self.base_sentiment, 2),
            "macro_bias": bias,
            "calendar": sorted(self.economic_events, key=lambda x: x["time_offset_min"])
        }

# Global singleton
news_engine = NewsIntelligence()
