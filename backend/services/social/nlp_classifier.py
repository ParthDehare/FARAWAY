"""NLP Classifier for social media posts.

Classifies railway-related social media posts into categories:
- hazard_report: Genuine hazard/incident reports
- passenger_report: Passenger delay/crowding complaints
- misinformation: False or exaggerated claims
- news_report: Legitimate news coverage
- irrelevant: Not railway safety related
"""

from typing import Optional
import re

HAZARD_PATTERNS = [
    r"boulder|landslide|derail|crash|accident|collapse|flood|waterlog",
    r"tracks?\s*(damage|broken|crack|block)",
    r"signal\s*failure",
    r"bridge\s*(damage|collapse|wash)",
]

MISINFORMATION_SIGNALS = [
    r"100s?\s*dead",
    r"massive\s*(crash|explosion)",
    r"breaking.*!!+",
    r"share\s*before\s*delete",
]

PASSENGER_PATTERNS = [
    r"(train|ट्रेन|ரயில்)\s*(delay|late|cancel|रद्द|लेट|தாமதம்)",
    r"stranded|overcrowd|no\s*information",
    r"platform.*crowd|भीड़",
]


class NLPClassifier:
    """Classifies social media posts for railway crisis relevance."""

    def classify(self, text: str, metadata: Optional[dict] = None) -> dict:
        text_lower = text.lower()
        metadata = metadata or {}

        misinfo_score = self._score_patterns(text_lower, MISINFORMATION_SIGNALS)
        hazard_score = self._score_patterns(text_lower, HAZARD_PATTERNS)
        passenger_score = self._score_patterns(text_lower, PASSENGER_PATTERNS)

        author = metadata.get("author", "")
        engagement = metadata.get("engagement", {})

        # Misinformation signals
        if misinfo_score > 0:
            low_engagement = engagement.get("likes", 0) < 50 and engagement.get("retweets", 0) < 10
            suspicious_author = any(w in author.lower() for w in ["bot", "fake", "breaking_"])
            if low_engagement or suspicious_author:
                return {
                    "classification": "misinformation",
                    "confidence": min(0.95, 0.6 + misinfo_score * 0.15),
                    "severity": "info",
                    "verified": False,
                    "reasoning": "Post matches misinformation patterns: sensationalized language, low engagement, suspicious source",
                }

        # Hazard report
        if hazard_score > 0:
            is_news = metadata.get("platform") == "news"
            high_engagement = engagement.get("retweets", 0) > 50
            confidence = min(0.98, 0.65 + hazard_score * 0.1 + (0.1 if high_engagement else 0) + (0.15 if is_news else 0))

            severity = "critical" if any(w in text_lower for w in ["boulder", "derail", "crash", "collapse"]) else "warning"

            return {
                "classification": "news_report" if is_news else "hazard_report",
                "confidence": confidence,
                "severity": severity,
                "verified": is_news or high_engagement,
                "reasoning": f"Hazard keywords detected (score: {hazard_score}). {'High engagement confirms legitimacy.' if high_engagement else 'Requires verification.'}",
            }

        # Passenger report
        if passenger_score > 0:
            return {
                "classification": "passenger_report",
                "confidence": min(0.90, 0.6 + passenger_score * 0.12),
                "severity": "warning" if engagement.get("likes", 0) > 100 else "info",
                "verified": True,
                "reasoning": "Passenger complaint/report patterns detected. Cross-referencing with live train status.",
            }

        return {
            "classification": "irrelevant",
            "confidence": 0.5,
            "severity": "info",
            "verified": False,
            "reasoning": "No railway safety patterns matched.",
        }

    def detect_language(self, text: str) -> str:
        devanagari = re.search(r'[\u0900-\u097F]', text)
        if devanagari:
            return "hi"
        tamil = re.search(r'[\u0B80-\u0BFF]', text)
        if tamil:
            return "ta"
        telugu = re.search(r'[\u0C00-\u0C7F]', text)
        if telugu:
            return "te"
        bengali = re.search(r'[\u0980-\u09FF]', text)
        if bengali:
            return "bn"
        gujarati = re.search(r'[\u0A80-\u0AFF]', text)
        if gujarati:
            return "gu"
        kannada = re.search(r'[\u0C80-\u0CFF]', text)
        if kannada:
            return "kn"
        malayalam = re.search(r'[\u0D00-\u0D7F]', text)
        if malayalam:
            return "ml"
        gurmukhi = re.search(r'[\u0A00-\u0A7F]', text)
        if gurmukhi:
            return "pa"
        odia = re.search(r'[\u0B00-\u0B7F]', text)
        if odia:
            return "or"
        return "en"

    def extract_location(self, text: str) -> Optional[dict]:
        station_patterns = [
            (r"near\s+(\w+\s*(?:junction|jn|station))", None),
            (r"between\s+(\w+)\s*[-–]\s*(\w+)", None),
            (r"KM[-\s]*(\d+)", None),
        ]
        for pattern, _ in station_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {"mention": match.group(0), "type": "extracted"}
        return None

    def _score_patterns(self, text: str, patterns: list[str]) -> int:
        score = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1
        return score
