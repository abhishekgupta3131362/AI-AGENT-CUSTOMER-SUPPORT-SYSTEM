import re
from typing import Dict, Any

class SentimentAnalyzer:
    """
    Real-time sentiment and frustration detector for customer support interactions.
    Scores sentiment from -1.0 (extremely negative/frustrated) to +1.0 (highly positive).
    """
    
    POSITIVE_WORDS = {
        "thank", "thanks", "great", "awesome", "excellent", "helpful", "good", 
        "love", "perfect", "appreciate", "wonderful", "amazing", "fast", "solved", 
        "resolved", "pleased", "happy", "glad", "satisfied", "super"
    }

    FRUSTRATION_WORDS = {
        "terrible", "awful", "horrible", "angry", "furious", "useless", "ridiculous", 
        "worst", "scam", "waste", "unacceptable", "broken", "garbage", "hate", 
        "disgusted", "annoying", "annoyed", "cheat", "cheat", "pathetic", "stupid",
        "incompetent", "sucks", "disaster", "fail", "failed", "never again", "rip off"
    }

    URGENCY_WORDS = {
        "urgent", "immediately", "asap", "right now", "emergency", "hurry", 
        "lawyer", "attorney", "sue", "fraud", "police", "chargeback"
    }

    def analyze(self, text: str) -> Dict[str, Any]:
        cleaned = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
        words = set(cleaned.split())

        pos_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in self.FRUSTRATION_WORDS)
        urg_count = sum(1 for w in words if w in self.URGENCY_WORDS)

        # Check for ALL CAPS shouting
        caps_words = [w for w in text.split() if w.isupper() and len(w) > 2]
        is_shouting = len(caps_words) >= 3

        # Exclamation mark intensity
        exclamation_count = text.count("!")
        
        # Calculate raw score
        score = 0.0
        if pos_count > 0:
            score += min(0.8, pos_count * 0.25)
        if neg_count > 0:
            score -= min(0.85, neg_count * 0.3)
        if urg_count > 0:
            score -= min(0.4, urg_count * 0.2)
        if is_shouting:
            score -= 0.35
        if exclamation_count >= 3:
            score -= 0.2

        score = max(-1.0, min(1.0, round(score, 2)))

        # Determine sentiment label and frustration flag
        if score <= -0.4 or neg_count >= 2 or urg_count >= 1 or is_shouting:
            label = "Frustrated"
            is_frustrated = True
        elif score < -0.1:
            label = "Dissatisfied"
            is_frustrated = False
        elif score >= 0.3:
            label = "Positive"
            is_frustrated = False
        else:
            label = "Neutral"
            is_frustrated = False

        return {
            "score": score,
            "label": label,
            "is_frustrated": is_frustrated,
            "is_urgent": urg_count > 0 or is_shouting,
            "indicators": {
                "positive_words": pos_count,
                "frustration_words": neg_count,
                "urgency_detected": urg_count > 0,
                "shouting_detected": is_shouting
            }
        }
